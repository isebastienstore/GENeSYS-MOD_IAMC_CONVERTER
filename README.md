# GENeSYS-MOD IAMC Converter

A standalone, profile-driven converter for transforming GENeSYS-MOD input
parameters and annual model results into the IAMC wide format used by the
OpenMod4Africa workflow.

## What the converter exports

The main `outputs` command recalculates the input-derived and output-derived
IAMC variables and writes one essential deliverable:

```text
export-directory/combined_iamc.xlsx
```

The workbook contains one `data` sheet with these IAMC dimensions:

```text
Model | Scenario | Region | Variable | Unit | <year columns>
```

Immediately before the workbook is written, the converter applies the public
export policy:

- the model name comes from the profile and defaults to `GENeSYS-MOD v3.1`;
- the aggregate `World` region is removed;
- all directional interconnection regions containing `>` are removed;
- the 179 variables rejected during the 2026 OpenMod4Africa nomenclature
  review are removed by exact name;
- duplicate observations are removed, while contradictory IAMC keys raise an
  error.

The frozen exclusion list is stored in
[`src/genesysmod_iamc/profiles/excluded_variables.txt`](src/genesysmod_iamc/profiles/excluded_variables.txt).
It is intentionally explicit so nomenclature changes can be reviewed in Git.

## Requirements

- Python 3.10 or newer
- a GENeSYS-MOD input workbook
- the annual GENeSYS-MOD CSV result files named in the conversion profile

Install the package in an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Generate the combined IAMC workbook

```bash
genesysmod-iamc outputs /path/to/genesysmod/outputs \
  --input-file /path/to/input_data.xlsx \
  --output export-directory
```

The output directory is created automatically. Existing
`combined_iamc.xlsx` files are replaced by the new export.

For diagnostic work, inputs can be converted separately:

```bash
genesysmod-iamc inputs /path/to/input_data.xlsx \
  --output export-directory
```

This optional command writes only `inputs_iamc.xlsx`.

## Configuration

The default profile is
[`src/genesysmod_iamc/profiles/conversion.yaml`](src/genesysmod_iamc/profiles/conversion.yaml).
Create and edit a copy of this profile for each case study. At minimum, review:

- `Model`: the model name and version written to the IAMC `Model` column;
- `Scenarios`: the mapping from the desired IAMC scenario name to the scenario
  labels present in the GENeSYS-MOD input and output files;
- `Scenario`: the one scenario selected for export;
- `genesys_datafiles.output`: the GENeSYS-MOD result filenames;
- `TechnosMappings` and `StorageMappings`: the source technology and storage
  identifiers and their IAMC names;
- `variables`: the source sheets, units and calculation rules required by the
  case study.

Years and regions are not configured as static lists in this profile. The
converter reads them from the input workbook:

- years come from the `Year` column of the `Sets` sheet;
- regions come from the `Region` column of the `Sets` sheet;
- `global_region` identifies the aggregate region, normally `World`, which is
  excluded from the public export;
- `--region-prefix` supplies the IAMC parent region added to native region
  names, for example `Senegal`.

Therefore, update the `Sets` sheet when the case-study years or regions change.
There is no active `years` or `listregionsGET` setting in the converter.

Use a project-specific copy when the source model changes:

```bash
genesysmod-iamc outputs /path/to/outputs \
  --input-file /path/to/input_data.xlsx \
  --settings /path/to/conversion.yaml \
  --region-prefix Senegal \
  --output export-directory
```

Canonical IAMC spellings are defined in the profile. For example, the default
mapping writes `Synthetic Methane` directly; the converter does not perform a
post-export spelling substitution.

## Nomenclature validation

Conversion and nomenclature validation are separate steps. From a checkout of
the OpenMod4Africa public workflow, run:

```bash
nomenclature validate-scenarios \
  /path/to/genesysmod-iamc-converter/export-directory/combined_iamc.xlsx
```

The 179-name exclusion list reflects one reviewed reference snapshot. If the
OpenMod4Africa nomenclature changes, validate again and update the list through
a reviewed commit instead of silently renaming variables.

## Tests

```bash
python -m unittest discover -s tests
```

The tests cover model naming, final export filtering, region normalization,
the frozen 179-variable list and, when the local regression dataset is
available, the complete conversion.

## Repository layout

```text
src/genesysmod_iamc/
├── cli.py                 command-line interface
├── converter.py           source loading and export orchestration
├── engine.py              configurable IAMC calculations
├── regions.py             region normalization
└── profiles/
    ├── conversion.yaml    default model and mapping profile
    └── excluded_variables.txt
tests/                     automated tests
export-directory/          generated files (ignored by Git)
```
