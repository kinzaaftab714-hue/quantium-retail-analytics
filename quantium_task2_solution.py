# ============================================================
# QUANTIUM DATA ANALYTICS - TASK 2
# Trial Store Selection & Uplift Evaluation
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ============================================================
# STEP 1: LOAD DATA (output from Task 1)
# ============================================================
data = pd.read_csv("QVI_data.csv")
data['DATE'] = pd.to_datetime(data['DATE'], dayfirst=True)
data['YEARMONTH'] = data['DATE'].dt.year * 100 + data['DATE'].dt.month

# ============================================================
# STEP 2: MONTHLY METRICS PER STORE
# ============================================================
monthly = data.groupby(['STORE_NBR', 'YEARMONTH']).agg(
    totSales   = ('TOT_SALES', 'sum'),
    nCustomers = ('LYLTY_CARD_NBR', 'nunique'),
    nTxns      = ('TXN_ID', 'count'),
    nChips     = ('PROD_QTY', 'sum'),
).reset_index()
monthly['nTxnPerCust']     = monthly['nTxns'] / monthly['nCustomers']
monthly['nChipsPerTxn']    = monthly['nChips'] / monthly['nTxns']
monthly['avgPricePerUnit'] = monthly['totSales'] / monthly['nChips']

# Keep only stores with full 12-month observation
full_stores = monthly.groupby('STORE_NBR')['YEARMONTH'].count()
full_stores = full_stores[full_stores == 12].index.tolist()
pre_trial = monthly[(monthly['YEARMONTH'] < 201902) & (monthly['STORE_NBR'].isin(full_stores))]

# ============================================================
# STEP 3: CONTROL STORE MATCHING FUNCTIONS
# ============================================================
def calc_correlation(tbl, metric, trial_store):
    """Pearson correlation of each candidate store's metric trend vs trial store."""
    stores = tbl['STORE_NBR'].unique()
    trial_vals = tbl[tbl['STORE_NBR'] == trial_store][['YEARMONTH', metric]].set_index('YEARMONTH')
    rows = []
    for s in stores:
        ctrl_vals = tbl[tbl['STORE_NBR'] == s][['YEARMONTH', metric]].set_index('YEARMONTH')
        merged = trial_vals.join(ctrl_vals, lsuffix='_t', rsuffix='_c').dropna()
        corr = merged.iloc[:, 0].corr(merged.iloc[:, 1]) if len(merged) > 1 else 0
        rows.append({'Store1': trial_store, 'Store2': s, 'corr_measure': corr})
    return pd.DataFrame(rows)


def calc_magnitude(tbl, metric, trial_store):
    """Standardized magnitude distance (0-1, closer to 1 = more similar)."""
    stores = tbl['STORE_NBR'].unique()
    trial_vals = tbl[tbl['STORE_NBR'] == trial_store][['YEARMONTH', metric]].set_index('YEARMONTH')
    rows = []
    for s in stores:
        ctrl_vals = tbl[tbl['STORE_NBR'] == s][['YEARMONTH', metric]].set_index('YEARMONTH')
        merged = trial_vals.join(ctrl_vals, lsuffix='_t', rsuffix='_c').dropna()
        for ym, row in merged.iterrows():
            rows.append({'Store1': trial_store, 'Store2': s, 'YEARMONTH': ym,
                         'measure': abs(row.iloc[0] - row.iloc[1])})
    dist = pd.DataFrame(rows)
    dist['minDist'] = dist.groupby(['Store1', 'YEARMONTH'])['measure'].transform('min')
    dist['maxDist'] = dist.groupby(['Store1', 'YEARMONTH'])['measure'].transform('max')
    dist['magMeasure'] = 1 - (dist['measure'] - dist['minDist']) / (dist['maxDist'] - dist['minDist'])
    final = dist.groupby(['Store1', 'Store2'])['magMeasure'].mean().reset_index()
    final.columns = ['Store1', 'Store2', 'mag_measure']
    return final


def find_control(trial_store, pre_data, corr_weight=0.5):
    """Combine correlation + magnitude scores for sales & customers to find best control store."""
    corr_s = calc_correlation(pre_data, 'totSales',   trial_store)
    corr_c = calc_correlation(pre_data, 'nCustomers', trial_store)
    mag_s  = calc_magnitude(pre_data,  'totSales',   trial_store)
    mag_c  = calc_magnitude(pre_data,  'nCustomers', trial_store)

    score_s = corr_s.merge(mag_s, on=['Store1', 'Store2'])
    score_s['scoreNSales'] = corr_weight*score_s['corr_measure'] + (1-corr_weight)*score_s['mag_measure']

    score_c = corr_c.merge(mag_c, on=['Store1', 'Store2'])
    score_c['scoreNCust'] = corr_weight*score_c['corr_measure'] + (1-corr_weight)*score_c['mag_measure']

    score = score_s[['Store1','Store2','scoreNSales']].merge(
            score_c[['Store1','Store2','scoreNCust']], on=['Store1','Store2'])
    score['finalScore'] = 0.5*score['scoreNSales'] + 0.5*score['scoreNCust']

    score = score[score['Store2'] != trial_store].sort_values('finalScore', ascending=False)
    control = int(score.iloc[0]['Store2'])
    print(f"Trial {trial_store} -> Control {control} (score={score.iloc[0]['finalScore']:.3f})")
    return control

# ============================================================
# STEP 4: FIND CONTROL STORES FOR EACH TRIAL STORE
# ============================================================
TRIAL_STORES = [77, 86, 88]
controls = {ts: find_control(ts, pre_trial) for ts in TRIAL_STORES}

# ============================================================
# STEP 5: UPLIFT EVALUATION (SCALING + T-TEST LOGIC)
# ============================================================
def evaluate_trial(trial_store, control_store, metric, monthly, pre_trial):
    """Scale control store to trial store's pre-trial baseline, then compute
    percentage difference and standard deviation for significance testing."""
    sf = pre_trial[pre_trial['STORE_NBR'] == trial_store][metric].sum() / \
         pre_trial[pre_trial['STORE_NBR'] == control_store][metric].sum()

    t = monthly[monthly['STORE_NBR'] == trial_store][['YEARMONTH', metric]].copy()
    c = monthly[monthly['STORE_NBR'] == control_store][['YEARMONTH', metric]].copy()
    c['scaled'] = c[metric] * sf

    merged = t.merge(c[['YEARMONTH', 'scaled']], on='YEARMONTH')
    merged['pctDiff'] = abs(merged[metric] - merged['scaled']) / merged['scaled']
    merged['DATE'] = pd.to_datetime(merged['YEARMONTH'].astype(str), format='%Y%m')

    std_dev = merged[merged['YEARMONTH'] < 201902]['pctDiff'].std()
    trial_period = merged[(merged['YEARMONTH'] >= 201902) & (merged['YEARMONTH'] <= 201904)]
    t_values = (trial_period[metric] - trial_period['scaled']) / (trial_period['scaled'] * std_dev)

    print(f"\nStore {trial_store} vs {control_store} — {metric}")
    print(trial_period[['YEARMONTH', metric, 'scaled']].assign(t_value=t_values.values))

    return merged, std_dev

# ============================================================
# STEP 6: RUN EVALUATION + PLOT FOR EACH TRIAL STORE
# ============================================================
NAVY, BLUE, GREY = '#1F2A5C', '#29ABE2', '#888888'

fig, axes = plt.subplots(len(TRIAL_STORES), 2, figsize=(16, 5*len(TRIAL_STORES)))
fig.suptitle('Trial Store Uplift Analysis (Feb-Apr 2019 Trial Period)',
             fontsize=15, fontweight='bold', color=NAVY)

for row, ts in enumerate(TRIAL_STORES):
    cs = controls[ts]
    m_sales, std_sales = evaluate_trial(ts, cs, 'totSales',   monthly, pre_trial)
    m_cust,  std_cust  = evaluate_trial(ts, cs, 'nCustomers', monthly, pre_trial)

    for ax, merged, std, ylabel, metric_col in [
        (axes[row,0], m_sales, std_sales, 'Total Sales ($)', 'totSales'),
        (axes[row,1], m_cust,  std_cust,  'Number of Customers', 'nCustomers'),
    ]:
        ymax = max(merged[metric_col].max(), merged['scaled'].max()) * 1.25
        ax.fill_betweenx([0, ymax], pd.Timestamp('2019-02-01'), pd.Timestamp('2019-04-30'),
                          alpha=0.15, color='orange')
        ax.plot(merged['DATE'], merged[metric_col], color=NAVY, lw=2.5, label=f'Trial {ts}')
        ax.plot(merged['DATE'], merged['scaled'], color=BLUE, lw=2, label=f'Control {cs} (scaled)')
        ax.plot(merged['DATE'], merged['scaled']*(1+std*2), '--', color=GREY, lw=1, label='95th pct CI')
        ax.plot(merged['DATE'], merged['scaled']*(1-std*2), ':', color=GREY, lw=1, label='5th pct CI')
        ax.set_ylim(0, ymax)
        ax.set_title(f'Store {ts} vs {cs} — {ylabel}', fontweight='bold', color=NAVY, fontsize=10)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
        ax.legend(fontsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('quantium_task2_analysis.pdf', bbox_inches='tight', dpi=150)
print("\nAnalysis complete. Charts saved to quantium_task2_analysis.pdf")
