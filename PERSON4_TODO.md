# Person 4 — export, QA, dashboard, and story

## Completed provisional export

The completed template is in `outputs/person4_delivery/Template Deliverable - provisional forecast.xlsx`.

It preserves the supplied ten sheets, headers, dates, and layout. It fills only the three cumulative-production columns using the current Person 2/3 shortlist.

| Template sheet | Selected original case |
| --- | ---: |
| Case 1 | 69 |
| Case 2 | 65 |
| Case 3 | 47 |
| Case 4 | 24 |
| Case 5 | 19 |
| Case 6 | 81 |
| Case 7 | 32 |
| Case 8 | 90 |
| Case 9 | 99 |
| Case 10 | 2 |

## QA completed

- [x] 10 template sheets retained.
- [x] 80 quarterly rows in every sheet.
- [x] 2,400 forecast values populated (10 forecasts × 80 dates × 3 fluids).
- [x] No missing values or decreasing cumulative curves across 30 fluid curves.
- [x] No formula errors found in the exported workbook.

`outputs/person4_delivery/template_qa.json` contains the machine-readable check results.

## Remaining Person 4 work

- [ ] Obtain Person 2/3 approval of shortlist and forecast assumptions. Re-export if they change.
- [ ] Use the approved workbook as the Power BI data source. Keep one page for forecast comparison and one for case/uncertainty context.
- [ ] Build the seven-minute presentation/video story: problem, data, history-match method, back-test, forecast range, risk, and conclusion.
- [ ] Perform final file-open check in Excel and confirm the competition portal rules before upload.

## Important limitation

The submitted curves are **modelled** after 1 Jan 2008 because the supplied case curves contain no later source values. Do not describe them as measured future production.
