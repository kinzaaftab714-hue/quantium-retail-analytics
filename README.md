# 🛒 Quantium Retail Strategy & Analytics

**Customer Segmentation, Purchasing Behaviour Analysis & A/B Trial Evaluation for a Retail Chips Category**

This project replicates a real-world retail analytics engagement completed as part of the **Quantium Data Analytics Virtual Experience Program (Forage)**. It analyzes 260,000+ retail transactions to uncover customer purchasing patterns and statistically evaluate the impact of an in-store trial on sales performance.

---

## 📌 Business Context

A retail Category Manager, **Julia**, needed two things:
1. A clear understanding of **who buys chips and why** — to inform category strategy and shelf placement.
2. A statistically valid assessment of whether a **new store layout trial** (run in 3 stores) actually increased sales — to decide whether to roll it out chain-wide.

---

## 🎯 Project Objectives

**Task 1 — Customer Analytics**
- Clean and validate a year of transaction data
- Engineer features (brand, pack size) from raw product names
- Segment customers by `LIFESTAGE` and `PREMIUM_CUSTOMER` tier
- Identify which segments drive the most revenue, and why

**Task 2 — Trial Store Impact Assessment**
- Algorithmically select the best-matching **control store** for each of 3 trial stores using correlation + magnitude distance scoring
- Statistically test (t-test, 5th/95th percentile confidence bands) whether the trial caused a significant uplift in sales and customer counts

---

## 🛠️ Tools & Methods

| Category | Tools / Techniques |
|---|---|
| Language | Python (pandas, numpy, matplotlib, seaborn, scipy) |
| Data Cleaning | Outlier detection, date parsing, regex feature extraction |
| Statistics | Independent t-tests, Pearson correlation, standardized magnitude distance |
| Visualization | Multi-panel comparative charts, confidence interval bands |

---

## 📂 Repository Structure

```
quantium-retail-analytics/

│

├── quantium_task1_solution.py      # Task 1: Data cleaning + segmentation analysis

├── quantium_task1_analysis.pdf     # Task 1: Output charts & insights

│

├── quantium_task2_solution.py      # Task 2: Control store matching + uplift testing

├── quantium_task2_analysis.pdf     # Task 2: Trial vs control comparison charts

│

└── README.md
```
**Note:** Raw datasets (`QVI_transaction_data.xlsx`, `QVI_purchase_behaviour.csv`, `QVI_data.csv`) are not included in this repository as per Forage's data usage policy. To run the scripts, place the original Quantium datasets in the project root.
## 🔑 Key Findings

### Task 1 — Who Drives Chip Sales?
- **Budget – Older Families**, **Mainstream – Young Singles/Couples**, and **Mainstream – Retirees** are the top 3 revenue-generating segments.
- Mainstream Young/Midage Singles & Couples pay a **statistically significant premium** per unit (p < 0.0001) — consistent with impulse-driven buying.
- This segment shows strong brand affinity toward **Tyrrells (+19%)** and a preference for **larger pack sizes (270g–380g)**.

**Commercial implication:** Off-locating premium/impulse brands like Tyrrells in high-traffic discretionary spaces could lift category sales among this segment.

### Task 2 — Did the Trial Work?
| Trial Store | Control Store | Result |
|---|---|---|
| 77 | 233 | ✅ Significant sales uplift |
| 86 | 155 | ⚠️ Customers up, sales flat — possible pricing/discounting effect |
| 88 | 237 | ✅ Significant sales & customer uplift |

**Recommendation:** Roll out the trial layout to stores resembling 77 and 88; investigate pricing strategy used in store 86 before wider rollout.

---

## 📊 Sample Output

*(Charts available in the `/analysis` PDFs — segment revenue breakdown, brand/pack affinity, and trial vs. control sales trends with confidence bands)*

---

## 🙋 About This Project

Completed as part of the **Quantium Virtual Internship via Forage**, and independently re-implemented in **Python** (the official program uses R) to demonstrate cross-language data analysis capability.

**Author:** Kinza Aftab
💻 [GitHub](https://github.com/kinzaaftab714-hue)

---

*This analysis uses anonymized, simulated retail transaction data provided by Quantium for educational purposes via Forage.*
