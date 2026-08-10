# Ecological Informatics revision: submission file map

## Main manuscript
- `Ecological_Informatics_ms_revised_purple.docx`
  - All experiment-driven revisions and additions made in this round are marked in purple.
  - Section 3.6 has been removed and its necessary content incorporated into Section 3.5 Statistical Analysis.
  - The Results include the corrected conditional ELS analysis, habitat threshold/score sensitivity, and annual CEq sensitivity.

## Supplementary Material
- `Supplementary_Material.docx`
  - Supplementary Methods S1-S2, Tables S1-S6, and Figures S1-S4.

## Supplementary Data
- `Data/Data_S1_Habitat_Class_Areas.csv`: observed S1-S5 areas under the three threshold schemes.
- `Data/Data_S2_Habitat_Exposure_Metrics.csv`: corrected habitat exposure metrics and continuous-radiance statistics.
- `Data/Data_S3_CEq_Annual_Sensitivity.csv`: annual corridor CEq and valid-area data.

## Supplementary Code
- `Code/Code_S1_Habitat_Robustness.py`: habitat threshold/score sensitivity and exact group comparisons.
- `Code/Code_S2_CEq_Annual_Sensitivity.py`: annual CEq robustness analysis.
- `Code/requirements.txt`: Python package requirements.

## Files intentionally not designated for journal submission
- `mann_whitney_habitat_project(1).zip`: superseded by the corrected exact-permutation analysis because the old project treated ELS=0 when A_lit=0.
- Monte Carlo and leave-one-out outputs from the full development package: useful diagnostics but not necessary to answer the reviewer and omitted to avoid overloading the manuscript.
- Development dashboards, bilingual working reports, intermediate workbooks, legacy XLS copies, and `__pycache__` folders.

## Before resubmission
1. Upload the main manuscript and `Supplementary_Material.docx` as separate manuscript/supplement files.
2. Upload Data S1-S3 and Code S1-S2 as supplementary data/code or deposit them in the cited repository/archive.
3. Create a versioned GitHub release or archival DOI and replace the remaining author-action placeholder in the Data and Code Availability statement.
4. Confirm the exact VNP46A4 collection/version, SDS layer, QA filtering, and no-data treatment in the manuscript against the actual GIS workflow.
