In this step, you will upload some datasets. The datasets supported formats are delimiter-separated ones, such as CSV (comma-separated) or TSV (tab-separated). A preview of the content of file will be proposed for validation. The dataset dictionary needs to be qualified, see the dictionary reference file available for download. Finally, the dataset is to be associated to one of the building space and instrument declared in the previous steps.

Please make sure that the headers in each CSV file include:

| Building_ID | Space_ID | Instrument_ID | Timestamp | Parameter1 | Parameter2 | ... |
|-------------|----------|---------------|-----------|------------|------------|-----|
| ...         | ...      | ...           | ...       | ...        | ...        | ... |
| ...         | ...      | ...           | ...       | ...        | ...        | ... |


Where the building, space and instrument IDs, along with the measurement parameters are the ones declared in the previous steps.

There is no strict nomenclature required for naming the CSV files or assigning Building IDs, Space IDs, etc., as long as they are unique and the IDs match those in the template and datasets.
