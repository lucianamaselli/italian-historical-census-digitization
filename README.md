# Digitizing Italian Historical Censuses with DataLab

As part of GENPOP at the University of Bologna, I worked on converting scanned Italian census tables into structured demographic data. I developed extraction strategies tailored to each census year because table layouts and page structure changed across editions. This repository illustrates one part of that work using the 1871 census.

This digitization work contributed to [DemoPast](https://demopast.it/), the Italian Historical Demographic Atlas built by the GENPOP team. The atlas provides [harmonized census tables](https://demopast.it/download.html) for eleven census years from 1861 to 1971.

## Adapting extraction to each census year

We combined page preprocessing and layout-specific Python rules with Marker through the DataLab API. Marker handled OCR and table reconstruction. Our scripts determined which pages or regions to submit, how to parse the returned HTML, and how to preserve the source of each extraction.

| Census | Layout or extraction problem | How we adapted the workflow |
| --- | --- | --- |
| 1871 | Tables could start in different parts of a page, and full-page extraction sometimes recovered only part of a table. | We tested six page variants, including the full page, page halves, and lower-page regions. The recovered script excluded candidate tables with fewer than five rows, ranked the remaining candidates by row count × column count, and recorded the source PDF, page, and selected variant. |
| 1951 | One series stored male and female tables in separate files. Another placed both blocks side by side with marital-status columns. | For the separate files, we identified sex from the filename. For the side-by-side layout, we flattened hierarchical headers and selected the male, female, and overall totals from the relevant columns. |
| 1961 | In one series, several consecutive pages could cover the same sex. In a second layout, some provincial scans were difficult to parse. | For the first series, we identified `Maschi` or `Femmine` from the returned HTML. For persistent failures in the second, we tried alternative HTML parsing and used local Tesseract OCR on selected scans. |

The 1871 size score helped screen for partial extractions. We checked the consolidated provincial tables against the source PDFs and manually corrected discrepancies before harmonization.

The public Python example splits selected PDF pages, submits each page to DataLab, and converts the first returned HTML table to CSV. It preserves the source PDF name and page number so extracted values can be checked against the original scan. This example adapts my original Marker workflow to DataLab’s Convert endpoint and covers the full-page extraction step. The output is an intermediate table for review and harmonization.

## Run the offline example

With Python 3.10 or later, run:

```bash
python -m pip install -r requirements.txt
python extract_tables.py html example.html --source-pdf example_1871.pdf --page 1
```

The synthetic HTML contains fictional values and a two-level table header. The command writes `output/example_1871_p001.csv`, which can be compared with `example_output.csv`.

## Extract tables from a scan

Set `DATALAB_API_KEY` in your environment and run:

```bash
python extract_tables.py pdf path/to/census_1871.pdf --pages 1 2
```

Page numbers are 1-based. This command uploads the selected pages to DataLab and can use API credits. Existing CSVs are skipped in PDF mode so a batch can be resumed. Use a separate output directory for each source volume if filenames overlap.

The script selects the first HTML table on each page, following the original 1871 workflow. Check that the first table is the intended one and compare headers and values with the scan before harmonizing the extracted data. The offline conversion is verified with the included fixture. The live API path has not been exercised with credentials for this public example.
