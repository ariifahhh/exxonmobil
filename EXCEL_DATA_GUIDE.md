# Excel data guide

This guide explains the supplied Excel files. Keep every original workbook unchanged. Read them through code and write any cleaned output to a separate `data/processed/` folder.

## How the files connect

```text
01 Introduction.xlsx
  └─ field definitions + case uncertainty values

03–06 Train Cases.xlsx (Cases 1–70) ─┐
07 Validation Cases.xlsx (71–85) ────┼─ Reservoir grid properties for each realization
08 Test Cases.xlsx (86–100) ─────────┘
                                      │ case_id
02 Field Production.xlsx ─────────────┘─ Production history and simulated production curves
                                      │ selected 10 forecasts
09 Template Deliverable.xlsx ◄────────┘─ Final submission workbook
```

## 01 Introduction.xlsx

### `Nomenclature`

Reference sheet defining abbreviations. Use it as the source of truth for variable meaning and units.

| Group | Variables |
| --- | --- |
| Grid location | `I`, `J`, `K` indices; `X`, `Y`, `Z` coordinates |
| Static rock/flow properties | `PORV`, `PORO`, `PERMX`, `PERMY`, `PERMZ`, `NTG`, `TRANX`, `TRANY`, `TRANZ`, `PVTNUM` |
| Saturation/capillary endpoints | `SWL`, `SWLPC`, `SWCR`, `SWU`, `SGL`, `SGLPC`, `SGCR`, `SOWCR`, `SOGCR`, `PCW`, `PCG` |
| Dynamic properties | `PRESSURE`, `SWAT`, `SOIL`, `SGAS`, `RS`, `RV` |

### `Uncertainty Values`

100 rows, one per case. Columns are `Item`, `Fault Transmissibility`, `Porosity Multiplier`, `Permeability Multiplier`, and `Aquifer Pore Volume`. Join this table to other case data through the case number, for example `Case 1`.

## 02 Field Production.xlsx

This workbook contains the history-matching target and production curves for the realizations.

### `Field Production`

41 quarterly field observations from **1 Jan 1998 to 1 Jan 2008**.

| Column | Meaning |
| --- | --- |
| `Identifier` | Field identifier |
| `Date` | Quarterly observation date |
| `Oil production rate (STB/d)` | Observed oil rate |
| `Gas production rate (MSCF/d)` | Observed gas rate |
| `Water production rate (STB/d)` | Observed water rate |
| `Water injection rate (STB/d)` | Observed injection rate |

Use this sheet as the observed history. Do not use future values from the template period as if they were measured field history.

### Six case-curve sheets

- `Gas production cumulative`
- `Gas production rate`
- `Oil production cumulative`
- `Oil production rate`
- `Water production cumulative`
- `Water production rate`

These sheets have a three-row header, then a time series:

| Header row | Meaning |
| --- | --- |
| Row 1 | Plot labels such as `X`, `Y1`, `Y2` |
| Row 2 | Actual data labels: `Date`, `Case_1` … `Case_100`, and `RAMP_History` |
| Row 3 | Measurement/unit label for each case column |
| Row 4 onward | Dates and values |

`Case_1` to `Case_100` match the case tabs in the other workbooks. `RAMP_History` is a separate reference/history curve. The raw curves are not quarterly and can have irregular timestamps, so aggregate or interpolate only after documenting the rule.

**Confirmed coverage:** all six simulated curve sheets run from **1 Jan 1998 to 1 Jan 2008 only**. They provide history-matching data, not the 2008–2028 forecast values required by the template. Do not extrapolate them blindly. The forecasting stage must generate future cumulative production after matching/selecting the historical realizations.

## 03–06 Train Cases.xlsx

These four files hold **70 training realizations**:

| File | Case sheets |
| --- | --- |
| `03 Train Cases 1.xlsx` | Cases 1–20 |
| `04 Train Cases 2.xlsx` | Cases 21–40 |
| `05 Train Cases 3.xlsx` | Cases 41–60 |
| `06 Train Cases 4.xlsx` | Cases 61–70 |

Each sheet contains **90,365 data rows** plus the header. Each row is one reservoir grid cell. The 29 columns are:

1. `I Index`, `J Index`, `K Index`
2. `X Coordinate`, `Y Coordinate`, `Z Coordinate`
3. `Pore Volume (PORV)`, `Porosity (PORO)`
4. `Permeability I/J/K (PERMX, PERMY, PERMZ)`
5. `Net-to-Gross Ratio (NTG)`
6. `Transmissibility I/J/K (TRANX, TRANY, TRANZ)`
7. `Fluid In Place Region (FIPNUM)`, `PVT Region (PVTNUM)`
8. `Connate Water Saturation (SWL)`, `Critical Water Saturation (SWCR)`, `Maximum Water Saturation (SWU)`
9. `Connate Gas Saturation (SGL)`, `Critical Gas Saturation (SGCR)`, `Residual Oil to Water (SOWCR)`
10. `Pressure (PRESSURE)`, `Water Saturation (SWAT)`, `Oil Saturation (SOIL)`, `Gas Saturation (SGAS)`, `Solution Gas-Oil Ratio (RS)`, `Vapor Oil-Gas Ratio (RV)`

The Excel header spells one field as `Connateg Gas Saturation (SGL)`. Standardise the processed column name to `SGL`, but preserve the raw file unchanged.

## 07 Validation Cases.xlsx

Cases **71–85**, with exactly the same 29-column grid structure as training. Use these 15 cases to choose features, score weights, and ML hyperparameters. Do not treat them as final test data.

## 08 Test Cases.xlsx

Cases **86–100**, also with the same 29-column grid structure. Reserve these 15 cases for the final method. Do not use them to tune model settings or choose preprocessing rules.

## 09 Template Deliverable.xlsx

The submission workbook contains sheets `Case 1` through `Case 10`.

| Field | Requirement |
| --- | --- |
| Dates | 80 pre-filled quarterly dates: **1 Apr 2008 to 1 Jan 2028** |
| Outputs | Cumulative gas (MSCF), cumulative oil (STB), cumulative water (STB) |
| Data entry | Fill output values only; retain sheet names, headers, dates, formulas, and layout |
| Meaning | Each sheet represents one of the 10 selected forecast realizations, not necessarily original case IDs 1–10 |

## Cleaning rules before modelling

1. Load each case sheet with its source filename and `case_id` retained.
2. Standardise labels, date type, numeric types, and units in processed data.
3. Check duplicate case/date records, missing values, negative values, and cumulative curves that decrease.
4. Keep an audit table of every flagged record and every interpolation/aggregation decision.
5. Never overwrite source Excel files or silently drop values. Flag an issue first and decide the handling rule as a team.
