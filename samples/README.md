# Sample Data

Use these samples to exercise the MVP workflow.

## Application JSON

- `applications/passing-bourbon.json` — expected values for a passing label.
- `applications/abv-mismatch.json` — expected ABV differs from the generated label, producing FAIL for Alcohol Content.

## Label Images

Generated PNG labels should be created during setup or via the included sample-generation command if Pillow is available.

Planned image files:

- `labels/passing-bourbon-label.png`
- `labels/government-warning-failure-label.png`

The frontend also includes a "Load sample data" button for the passing bourbon scenario.
