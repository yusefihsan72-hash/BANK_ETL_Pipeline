"""
Data Visualization for BANK_ETL_Pipeline
Creates multiple charts showing warehouse data insights
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (16, 12)

# Connect to warehouse
conn = sqlite3.connect('warehouse/bank_warehouse.db')

print("📊 Generating Data Visualizations...")
print("=" * 70)

# Create a figure with multiple subplots
fig = plt.figure(figsize=(16, 12))
fig.suptitle('BANK ETL PIPELINE - DATA ANALYSIS DASHBOARD', fontsize=16, fontweight='bold', y=0.995)

# 1. Customers by Region
ax1 = plt.subplot(2, 3, 1)
df_region = pd.read_sql_query("""
    SELECT region, COUNT(*) as count 
    FROM dim_customer 
    WHERE region != 'NAN'
    GROUP BY region 
    ORDER BY count DESC
""", conn)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
ax1.bar(df_region['region'], df_region['count'], color=colors)
ax1.set_title('Customers by Region', fontsize=12, fontweight='bold')
ax1.set_ylabel('Count')
ax1.set_xlabel('Region')
for i, v in enumerate(df_region['count']):
    ax1.text(i, v + 5, str(v), ha='center', fontweight='bold')

# 2. Customers by Gender
ax2 = plt.subplot(2, 3, 2)
df_gender = pd.read_sql_query("""
    SELECT sex, COUNT(*) as count 
    FROM dim_customer 
    WHERE sex IN ('M', 'F')
    GROUP BY sex
""", conn)
colors_gender = ['#1f77b4', '#ff7f0e']
ax2.bar(['Male', 'Female'], df_gender['count'].values, color=colors_gender)
ax2.set_title('Gender Distribution', fontsize=12, fontweight='bold')
ax2.set_ylabel('Count')
for i, v in enumerate(df_gender['count'].values):
    ax2.text(i, v + 5, str(v), ha='center', fontweight='bold')

# 3. Age Distribution
ax3 = plt.subplot(2, 3, 3)
df_age = pd.read_sql_query("""
    SELECT age FROM dim_customer WHERE age IS NOT NULL
""", conn)
ax3.hist(df_age['age'].dropna(), bins=20, color='#2ca02c', edgecolor='black', alpha=0.7)
ax3.set_title('Age Distribution', fontsize=12, fontweight='bold')
ax3.set_xlabel('Age')
ax3.set_ylabel('Frequency')
ax3.axvline(df_age['age'].mean(), color='red', linestyle='--', linewidth=2, label=f"Avg: {df_age['age'].mean():.1f}")
ax3.legend()

# 4. Income Distribution
ax4 = plt.subplot(2, 3, 4)
df_income = pd.read_sql_query("""
    SELECT income FROM dim_customer WHERE income IS NOT NULL AND income > 0
""", conn)
ax4.hist(df_income['income'].dropna(), bins=30, color='#d62728', edgecolor='black', alpha=0.7)
ax4.set_title('Income Distribution', fontsize=12, fontweight='bold')
ax4.set_xlabel('Income ($)')
ax4.set_ylabel('Frequency')
ax4.axvline(df_income['income'].mean(), color='navy', linestyle='--', linewidth=2, label=f"Avg: ${df_income['income'].mean():,.0f}")
ax4.legend()

# 5. Transaction Types
ax5 = plt.subplot(2, 3, 5)
df_trans_type = pd.read_sql_query("""
    SELECT dt.transaction_type, COUNT(*) as count
    FROM fact_transactions ft
    JOIN dim_transaction_type dt ON ft.transaction_type_sk = dt.transaction_type_sk
    GROUP BY dt.transaction_type
    ORDER BY count DESC
""", conn)
ax5.barh(df_trans_type['transaction_type'], df_trans_type['count'], color='#9467bd')
ax5.set_title('Transaction Types', fontsize=12, fontweight='bold')
ax5.set_xlabel('Count')
for i, v in enumerate(df_trans_type['count'].values):
    ax5.text(v + 20, i, str(v), va='center', fontweight='bold')

# 6. Account Products (Mortgage, PEP, Car)
ax6 = plt.subplot(2, 3, 6)
df_products = pd.read_sql_query("""
    SELECT 
        SUM(CASE WHEN mortgage = 1 THEN 1 ELSE 0 END) as Mortgage,
        SUM(CASE WHEN pep = 1 THEN 1 ELSE 0 END) as PEP,
        SUM(CASE WHEN car = 1 THEN 1 ELSE 0 END) as Car
    FROM dim_customer
""", conn)

products = ['Mortgage', 'PEP', 'Car']
counts = [int(df_products['Mortgage'].values[0]), int(df_products['PEP'].values[0]), int(df_products['Car'].values[0])]
colors_products = ['#1f77b4', '#ff7f0e', '#2ca02c']
ax6.bar(products, counts, color=colors_products)
ax6.set_title('Account Products', fontsize=12, fontweight='bold')
ax6.set_ylabel('Count')
for i, v in enumerate(counts):
    ax6.text(i, v + 10, str(v), ha='center', fontweight='bold')

# Save figure
output_path = Path('reports/dashboard_visualization.png')
output_path.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(output_path, dpi=100, bbox_inches='tight')
print(f"\n✅ Saved visualization to: {output_path}")

# Display statistics
print("\n" + "=" * 70)
print("📈 KEY STATISTICS")
print("=" * 70)

df_stats = pd.read_sql_query("""
    SELECT 
        (SELECT COUNT(*) FROM dim_customer) as total_customers,
        (SELECT COUNT(*) FROM fact_transactions) as total_transactions,
        (SELECT ROUND(AVG(income), 2) FROM dim_customer WHERE income > 0) as avg_income,
        (SELECT ROUND(AVG(age), 1) FROM dim_customer WHERE age IS NOT NULL) as avg_age,
        (SELECT COUNT(*) FROM dim_customer WHERE married = 1) as married_customers,
        (SELECT COUNT(*) FROM dim_customer WHERE mortgage = 1) as mortgage_count
""", conn)

print(f"\n👥 Customers:")
print(f"   • Total Customers: {int(df_stats['total_customers'].values[0]):,}")
print(f"   • Average Age: {df_stats['avg_age'].values[0]:.1f} years")
print(f"   • Average Income: ${df_stats['avg_income'].values[0]:,.2f}")
print(f"   • Married: {int(df_stats['married_customers'].values[0]):,}")
print(f"   • With Mortgage: {int(df_stats['mortgage_count'].values[0]):,}")

print(f"\n💳 Transactions:")
print(f"   • Total Transactions: {int(df_stats['total_transactions'].values[0]):,}")

df_trans_stats = pd.read_sql_query("""
    SELECT 
        COUNT(*) as count,
        ROUND(AVG(amount), 2) as avg_amount,
        ROUND(MIN(amount), 2) as min_amount,
        ROUND(MAX(amount), 2) as max_amount,
        ROUND(SUM(amount), 2) as total_amount
    FROM fact_transactions
""", conn)

print(f"   • Average Amount: ${df_trans_stats['avg_amount'].values[0]:,.2f}")
print(f"   • Min Amount: ${df_trans_stats['min_amount'].values[0]:,.2f}")
print(f"   • Max Amount: ${df_trans_stats['max_amount'].values[0]:,.2f}")
print(f"   • Total Volume: ${df_trans_stats['total_amount'].values[0]:,.2f}")

print("\n" + "=" * 70)
print("✨ Dashboard ready! Open the visualization to view charts.")
print("=" * 70)

# Try to open the image
try:
    import webbrowser
    import os
    abs_path = os.path.abspath(output_path)
    print(f"\n📂 File location: {abs_path}")
except:
    pass

conn.close()
plt.show()
