# ============================================================
# QUANTIUM DATA ANALYTICS - TASK 1
# Customer Segment & Chip Purchasing Behaviour Analysis
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import re
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# STEP 1: LOAD DATA
# ============================================================
print("=" * 60)
print("STEP 1: LOADING DATA")
print("=" * 60)

# Load transaction data
transactions = pd.read_excel("QVI_transaction_data.xlsx")
behaviour    = pd.read_csv("QVI_purchase_behaviour.csv")

print(f"Transactions: {transactions.shape[0]:,} rows, {transactions.shape[1]} columns")
print(f"Behaviour:    {behaviour.shape[0]:,} rows, {behaviour.shape[1]} columns")

print("\nTransaction Columns:", list(transactions.columns))
print("Behaviour Columns:  ", list(behaviour.columns))

print("\nTransactions Sample:\n", transactions.head())
print("\nBehaviour Sample:\n",    behaviour.head())

# ============================================================
# STEP 2: DATA CHECKS & CLEANING
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: DATA CHECKS & CLEANING")
print("=" * 60)

# --- 2a. Check data types ---
print("\nData Types (Transactions):\n", transactions.dtypes)
print("\nData Types (Behaviour):\n",    behaviour.dtypes)

# --- 2b. Check nulls ---
print("\nNulls (Transactions):\n", transactions.isnull().sum())
print("\nNulls (Behaviour):\n",    behaviour.isnull().sum())

# --- 2c. Fix date column ---
# DATE is often stored as integer (days since 1899-12-30 in Excel)
if transactions['DATE'].dtype != 'datetime64[ns]':
    transactions['DATE'] = pd.to_datetime(
        transactions['DATE'], origin='1899-12-30', unit='D'
    )
print("\nDate Range:", transactions['DATE'].min(), "→", transactions['DATE'].max())

# --- 2d. Check PROD_NAME for non-chip products ---
print("\nUnique products (sample):", transactions['PROD_NAME'].unique()[:10])

# Remove salsa / non-chip products (they sneak into chip data)
transactions = transactions[
    ~transactions['PROD_NAME'].str.upper().str.contains('SALSA', na=False)
]
print(f"After removing salsa: {transactions.shape[0]:,} rows")

# --- 2e. Check for outliers in PROD_QTY ---
print("\nPROD_QTY Stats:\n", transactions['PROD_QTY'].describe())

# Any customer buying 200 units is suspicious (bulk/reseller)
outliers = transactions[transactions['PROD_QTY'] > 100]
print(f"\nOutlier transactions (qty > 100): {len(outliers)}")
if len(outliers) > 0:
    print(outliers[['LYLTY_CARD_NBR','DATE','PROD_QTY','TOT_SALES']])
    # Remove those customers entirely
    outlier_cards = outliers['LYLTY_CARD_NBR'].unique()
    transactions = transactions[
        ~transactions['LYLTY_CARD_NBR'].isin(outlier_cards)
    ]
    print(f"After removing outlier customers: {transactions.shape[0]:,} rows")

# ============================================================
# STEP 3: DERIVE NEW FEATURES
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: DERIVING NEW FEATURES")
print("=" * 60)

# --- 3a. Pack Size (grams) from product name ---
def extract_pack_size(name):
    match = re.search(r'(\d+)\s*[Gg]', str(name))
    return int(match.group(1)) if match else np.nan

transactions['PACK_SIZE'] = transactions['PROD_NAME'].apply(extract_pack_size)
print("Pack Size Distribution (top 10):")
print(transactions['PACK_SIZE'].value_counts().head(10))

# --- 3b. Brand Name (first word of product name) ---
transactions['BRAND'] = transactions['PROD_NAME'].apply(
    lambda x: str(x).strip().split()[0].upper()
)
# Standardise known aliases
brand_map = {
    'RED': 'RRD', 'SNBTS': 'SUNBITES', 'INFZNS': 'INFUZIONS',
    'WW': 'WOOLWORTHS', 'SMITHS': 'SMITHS', 'NCC': 'NATURAL',
    'DORITO': 'DORITOS', 'GRAIN': 'GRNWVES'
}
transactions['BRAND'] = transactions['BRAND'].replace(brand_map)
print("\nTop 10 Brands:\n", transactions['BRAND'].value_counts().head(10))

# ============================================================
# STEP 4: MERGE DATASETS
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: MERGING TRANSACTION + BEHAVIOUR DATA")
print("=" * 60)

data = transactions.merge(behaviour, on='LYLTY_CARD_NBR', how='left')
print(f"Merged dataset: {data.shape[0]:,} rows")
print("Nulls after merge:\n", data[['LIFESTAGE','PREMIUM_CUSTOMER']].isnull().sum())

# ============================================================
# STEP 5: DEFINE KEY METRICS
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: KEY METRICS BY CUSTOMER SEGMENT")
print("=" * 60)

# Group by LIFESTAGE and PREMIUM_CUSTOMER
segment_metrics = data.groupby(['LIFESTAGE','PREMIUM_CUSTOMER']).agg(
    Total_Sales       = ('TOT_SALES',    'sum'),
    Num_Customers     = ('LYLTY_CARD_NBR','nunique'),
    Num_Transactions  = ('TXN_ID',        'count'),
    Total_Units       = ('PROD_QTY',      'sum'),
    Avg_Price_Per_Unit= ('TOT_SALES',     lambda x:
                         x.sum() / data.loc[x.index,'PROD_QTY'].sum()),
    Avg_Spend_Per_Cust= ('TOT_SALES',     lambda x:
                         x.sum() / data.loc[x.index,'LYLTY_CARD_NBR'].nunique()),
    Avg_Units_Per_Txn = ('PROD_QTY',      'mean'),
).reset_index()

print(segment_metrics.sort_values('Total_Sales', ascending=False).head(10).to_string(index=False))

# ============================================================
# STEP 6: VISUALISATIONS
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: GENERATING CHARTS")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('Quantium – Chip Purchasing Behaviour Analysis\nTask 1: Customer Segment Insights',
             fontsize=15, fontweight='bold', y=1.01)
palette = 'Blues_d'

# --- Chart 1: Total Sales by Segment ---
ax1 = axes[0, 0]
top_segments = segment_metrics.nlargest(8, 'Total_Sales')
sns.barplot(data=top_segments, y='LIFESTAGE', x='Total_Sales',
            hue='PREMIUM_CUSTOMER', ax=ax1, palette=['#1F2A5C','#29ABE2','#7FB3D5'])
ax1.set_title('Total Sales by Customer Segment', fontweight='bold')
ax1.set_xlabel('Total Sales ($)')
ax1.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax1.set_ylabel('')

# --- Chart 2: Average Price Per Unit ---
ax2 = axes[0, 1]
pivot_price = segment_metrics.pivot_table(
    index='LIFESTAGE', columns='PREMIUM_CUSTOMER', values='Avg_Price_Per_Unit'
)
pivot_price.plot(kind='bar', ax=ax2, color=['#1F2A5C','#29ABE2','#7FB3D5'])
ax2.set_title('Average Price Per Unit by Segment', fontweight='bold')
ax2.set_ylabel('Avg Price ($)')
ax2.set_xlabel('')
ax2.tick_params(axis='x', rotation=45)
ax2.legend(title='Customer Type')

# --- Chart 3: Number of Customers ---
ax3 = axes[1, 0]
pivot_cust = segment_metrics.pivot_table(
    index='LIFESTAGE', columns='PREMIUM_CUSTOMER', values='Num_Customers'
)
pivot_cust.plot(kind='bar', ax=ax3, color=['#1F2A5C','#29ABE2','#7FB3D5'])
ax3.set_title('Number of Unique Customers by Segment', fontweight='bold')
ax3.set_ylabel('Number of Customers')
ax3.set_xlabel('')
ax3.tick_params(axis='x', rotation=45)

# --- Chart 4: Pack Size Distribution ---
ax4 = axes[1, 1]
pack_sales = data.groupby('PACK_SIZE')['TOT_SALES'].sum().reset_index()
sns.barplot(data=pack_sales.sort_values('PACK_SIZE'), x='PACK_SIZE',
            y='TOT_SALES', ax=ax4, color='#1F2A5C')
ax4.set_title('Total Sales by Pack Size (grams)', fontweight='bold')
ax4.set_xlabel('Pack Size (g)')
ax4.set_ylabel('Total Sales ($)')
ax4.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax4.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('quantium_task1_charts.pdf', bbox_inches='tight', dpi=150)
plt.savefig('quantium_task1_charts.png', bbox_inches='tight', dpi=150)
print("Charts saved → quantium_task1_charts.pdf & .png")

# ============================================================
# STEP 7: KEY INSIGHTS SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("STEP 7: KEY INSIGHTS FOR JULIA (CATEGORY MANAGER)")
print("=" * 60)

top3 = segment_metrics.nlargest(3, 'Total_Sales')[
    ['LIFESTAGE','PREMIUM_CUSTOMER','Total_Sales','Num_Customers','Avg_Price_Per_Unit']
]
print("\n🔑 Top 3 Revenue Segments:")
print(top3.to_string(index=False))

highest_price = segment_metrics.nlargest(3, 'Avg_Price_Per_Unit')[
    ['LIFESTAGE','PREMIUM_CUSTOMER','Avg_Price_Per_Unit']
]
print("\n🔑 Highest Avg Price Per Unit (premium spenders):")
print(highest_price.to_string(index=False))

most_units = segment_metrics.nlargest(3, 'Total_Units')[
    ['LIFESTAGE','PREMIUM_CUSTOMER','Total_Units']
]
print("\n🔑 Highest Volume Buyers (most units purchased):")
print(most_units.to_string(index=False))

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE ✅")
print("Upload 'quantium_task1_charts.pdf' to Forage to unlock model answer")
print("=" * 60)
