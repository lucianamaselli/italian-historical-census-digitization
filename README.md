# Digitizing Italian Historical Censuses with DataLab

As part of GENPOP at the University of Bologna, I worked on converting scanned Italian census tables into structured demographic data. I developed extraction strategies tailored to each census year because table layouts and page structure changed across editions. This repository illustrates one part of that work using the 1871 census.

This digitization work contributed to [DemoPast](https://demopast.it/), the Italian Historical Demographic Atlas built by the GENPOP team. The atlas provides [harmonized census tables](https://demopast.it/download.html) for eleven census years from 1861 to 1971.

## Adapting extraction to each census year

I combined computer vision preprocessing with DataLab’s document conversion API. The layout of each edition shaped how I prepared pages, which regions I submitted for extraction, and how I interpreted the resulting tables. For example, in the 1871 work I tried full-page extraction as well as targeted crops, including page halves and lower-page regions, to isolate tables in difficult scans. The API handled document conversion, while the layout guided the choice of what to send and what to check in the returned table.

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
