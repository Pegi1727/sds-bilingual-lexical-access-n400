# From L1-Mediated Translation to Direct L2 Conceptualization: A 6-Month Longitudinal ERP (N400) and Behavioral Investigation of the Semantic-Direct-System (S-D-S)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22161369.svg)](https://doi.org/10.5281/zenodo.22161369)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![R 4.3+](https://img.shields.io/badge/R-4.3%2B-276DC3.svg)](https://www.r-project.org/)
[![FAIR Data](https://img.shields.io/badge/Data-FAIR_Compliant-success.svg)](https://force11.org/info/fair-principles/)

---

## 📌 Graphical Abstract

<p align="center">
  <img src="figures/ga.png" alt="Graphical Abstract - S-D-S Bilingual Lexical Access & N400 Dynamics" width="100%" />
</p>

---

## 🔬 Key Empirical Findings & Results Summary

This repository contains the complete replication package, raw tabular datasets, BioSemi BDF neurophysiological streams, and statistical scripts for the 6-month longitudinal randomized controlled trial ($N = 40$; Experimental Group [EG] with S-D-S intervention vs. Active Control Group [CG], assessed at Months 1, 3, and 6).

### 1. Primary Behavioral & ERP Metrics Across Time (Mean ± SD)

| Metric | Group | Month 1 (Baseline) | Month 3 (Mid-Intervention) | Month 6 (Post-Intervention) | $\Delta \text{M6} - \text{M1}$ | Effect Size ($d$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **N400 Mean Amplitude ($\mu\text{V}$)** | **EG** | $-1.12 \pm 0.48$ | $-2.85 \pm 0.52$ | $-4.88 \pm 0.61$ | **$-3.76$** | **$d = 2.45$** (Very Large) |
| *(Centroparietal ROI: Cz, CPz, Pz)* | **CG** | $-1.08 \pm 0.45$ | $-1.42 \pm 0.49$ | $-1.85 \pm 0.54$ | $-0.77$ | $d = 0.42$ (Small) |
| **L1 Dependency Rate (%)** | **EG** | $68.4\% \pm 5.2\%$ | $41.2\% \pm 4.8\%$ | $18.6\% \pm 3.9\%$ | **$-49.8\%$** | **$d = 3.12$** |
| *(Think-Aloud Protocols)* | **CG** | $67.9\% \pm 5.0\%$ | $61.5\% \pm 5.3\%$ | $55.2\% \pm 4.7\%$ | $-12.7\%$ | $d = 0.74$ |
| **Speech Latency (ms)** | **EG** | $1420 \pm 115$ | $1085 \pm 95$ | $745 \pm 68$ | **$-675\text{ ms}$** | **$d = 2.88$** |
| *(Picture-Naming Task)* | **CG** | $1410 \pm 110$ | $1320 \pm 105$ | $1210 \pm 98$ | $-200\text{ ms}$ | $d = 0.65$ |
| **Calque Transfer Errors (count)**| **EG** | $18.4 \pm 2.8$ | $8.2 \pm 2.1$ | $2.1 \pm 1.2$ | **$-16.3$** | **$d = 2.64$** |
| *(Standardized Elicitation)* | **CG** | $18.1 \pm 2.6$ | $15.4 \pm 2.4$ | $12.8 \pm 2.2$ | $-5.3$ | $d = 0.82$ |
| **L2 Oral Fluency (WPM)** | **EG** | $64.2 \pm 6.8$ | $88.5 \pm 7.4$ | $118.4 \pm 8.2$ | **$+54.2\text{ WPM}$**| **$d = 2.71$** |
| *(Words Per Minute)* | **CG** | $63.8 \pm 6.5$ | $71.2 \pm 6.9$ | $79.6 \pm 7.1$ | $+15.8\text{ WPM}$| $d = 0.76$ |

---

### 2. Longitudinal Modeling & Mediation Analyses
