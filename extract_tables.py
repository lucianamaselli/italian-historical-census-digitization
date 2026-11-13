"""Extract page-level census tables with source provenance."""

import argparse
from io import BytesIO, StringIO
import os
from pathlib import Path
import time
from urllib.parse import urlsplit

import pandas as pd

CONVERT_URL = "https://www.datalab.to/api/v1/convert"
DATALAB_HOSTS = {"www.datalab.to", "api.datalab.to", "datalab.to"}


def convert_page(session, name, page_bytes):
    response = session.post(
        CONVERT_URL,
        files={"file": (name, page_bytes, "application/pdf")},
        data={"output_format": "html", "mode": "accurate"},
        timeout=60,
        allow_redirects=False,
    )
    response.raise_for_status()
    job = response.json()
    check_url = job.get("request_check_url", "")
    target = urlsplit(check_url)
    if (
        target.scheme != "https"
        or target.netloc not in DATALAB_HOSTS
    ):
        raise RuntimeError("DataLab did not return a trusted polling URL.")

    for _ in range(120):
        response = session.get(check_url, timeout=30, allow_redirects=False)
        response.raise_for_status()
        result = response.json()
        if result.get("status") == "failed":
            raise RuntimeError("DataLab conversion failed.")
        if result.get("status") == "complete":
            if result.get("success") is False or not result.get("html"):
                raise RuntimeError("DataLab completed without an HTML result.")
            return result["html"]
        time.sleep(2)
    raise TimeoutError("DataLab conversion did not finish within 120 polls.")


def write_table(html, source_pdf, page_number, output_dir):
    """Save the first HTML table, preserving its scan and 1-based PDF page."""
    try:
        tables = pd.read_html(StringIO(html), thousands=None)
    except ValueError as error:
        raise ValueError(f"{source_pdf}, page {page_number}: no readable table.") from error
    table = tables[0].copy()
    if isinstance(table.columns, pd.MultiIndex):
        table.columns = [" | ".join(str(part) for part in col if pd.notna(part))
                         for col in table.columns]
    table.insert(0, "source_pdf", source_pdf)
    table.insert(1, "pdf_page", page_number)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{Path(source_pdf).stem}_p{page_number:03d}.csv"
    with destination.open("x", encoding="utf-8", newline="") as output:
        table.to_csv(output, index=False)
    print(destination)


def extract_pdf(pdf, page_numbers, output_dir):
    import requests
    from pypdf import PdfReader, PdfWriter

    key = os.environ.get("DATALAB_API_KEY")
    if not key:
        raise ValueError("Set DATALAB_API_KEY before processing a PDF.")
    reader = PdfReader(pdf)
    if any(number < 1 or number > len(reader.pages) for number in page_numbers):
        raise ValueError(f"Choose PDF pages between 1 and {len(reader.pages)}.")
    with requests.Session() as session:
        session.headers["X-Api-Key"] = key
        for number in dict.fromkeys(page_numbers):
            destination = output_dir / f"{pdf.stem}_p{number:03d}.csv"
            if destination.exists():
                print(f"Skipping existing output: {destination}")
                continue
            writer = PdfWriter()
            writer.add_page(reader.pages[number - 1])
            page = BytesIO()
            writer.write(page)
            html = convert_page(session, f"{pdf.stem}_p{number:03d}.pdf", page.getvalue())
            write_table(html, pdf.name, number, output_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    offline = modes.add_parser("html", help="Convert a saved HTML response locally.")
    offline.add_argument("input", type=Path)
    offline.add_argument("--source-pdf", required=True)
    offline.add_argument("--page", type=int, required=True)
    live = modes.add_parser("pdf", help="Submit selected PDF pages to DataLab.")
    live.add_argument("input", type=Path)
    live.add_argument("--pages", type=int, nargs="+", required=True)
    for mode in (offline, live):
        mode.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()
    if args.mode == "pdf":
        extract_pdf(args.input, args.pages, args.output_dir)
    else:
        if args.page < 1:
            parser.error("--page must be at least 1")
        write_table(args.input.read_text(encoding="utf-8"),
                    Path(args.source_pdf).name, args.page, args.output_dir)


if __name__ == "__main__":
    main()
