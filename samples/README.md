# Sample Data

Use these included samples to exercise the MVP workflow immediately. No sample-generation step is required.

## Application JSON

- `applications/passing-bourbon.json` — expected values for the passing bourbon label scenario.
- `applications/abv-mismatch.json` — expected values with an ABV mismatch; use with the passing bourbon label to produce a FAIL for Alcohol Content.

## Label Images

The repository includes these ready-to-use PNG label images:

- `labels/passing-bourbon-label.png` — sample label intended to match `passing-bourbon.json`.
- `labels/government-warning-failure-label.png` — sample label with an invalid/incomplete government warning.

## Suggested Manual Checks

1. Passing case:
   - Click `Load sample data` in the frontend.
   - Upload `labels/passing-bourbon-label.png`.

2. ABV mismatch case:
   - Use values from `applications/abv-mismatch.json`.
   - Upload `labels/passing-bourbon-label.png`.

3. Government warning failure case:
   - Use values from `applications/passing-bourbon.json`.
   - Upload `labels/government-warning-failure-label.png`.
