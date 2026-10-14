# DataWorks Challenge 2026 — Competition & Dataset Guide

## Objective

Select ten reservoir realizations that best reproduce the observed field history, then provide quarterly cumulative gas, oil, and water forecasts from 1 April 2008 to 1 January 2028.

## Source workbooks

| Workbook | Contents | Processing status |
| --- | --- | --- |
| `01 Introduction.xlsx` | Nomenclature and four uncertainty values for 100 cases | Loaded and cleaned |
| `02 Field Production.xlsx` | Field history and six simulated production-curve sheets | Loaded, reshaped, validated and resampled |
| `03`–`06 Train Cases.xlsx` | Grid properties, cases 1–70 | Schema validated; features extracted for cases 1–5 only |
| `07 Validation Cases.xlsx` | Grid properties, cases 71–85 | Schema validated; feature extraction pending |
| `08 Test Cases.xlsx` | Grid properties, cases 86–100 | Schema validated; feature extraction pending |
| `09 Template Deliverable.xlsx` | 80 quarterly forecast dates and required output layout | Used as date template; not modified by preprocessing |

## Data contracts

### Case uncertainties

`case_id`, `fault_transmissibility`, `porosity_multiplier`, `permeability_multiplier`, `aquifer_pore_volume`

### Field history

`identifier`, `date`, `oil_rate_stb_d`, `gas_rate_mscf_d`, `water_rate_stb_d`, `water_injection_rate_stb_d`

### Simulated production

`case_id`, `date`, `fluid`, `rate`, `cumulative`

`fluid` is one of `gas`, `oil`, or `water`. The history window is 1 January 1998–1 January 2008. The source curves do not contain future values.

## Essential rules

- Never edit anything in `TestCases/`.
- Keep zero values distinct from missing values.
- Do not extrapolate source curves while cleaning.
- Keep cases 1–70 for training, 71–85 for validation, and 86–100 for final test evaluation.
- Preserve the dates, sheet names, units, and layout of the submission template.

See `EXCEL_DATA_GUIDE.md` for the detailed column-level description.
