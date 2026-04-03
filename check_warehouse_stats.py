import sqlite3
import pandas as pd

conn = sqlite3.connect('warehouse/bank_warehouse.db')
cursor = conn.cursor()

# Get table row counts
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\n" + "="*60)
print("WAREHOUSE STATUS AFTER PIPELINE RUN")
print("="*60)

for table in tables:
    table_name = table[0]
    df = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table_name}", conn)
    count = df['count'].values[0]
    print(f"{table_name:20} → {count:>10} rows")

print("="*60)

# Detailed stats
print("\n📊 CUSTOMER DIMENSION:")
df_customers = pd.read_sql_query("SELECT COUNT(*) as total, sex, region FROM dim_customer GROUP BY sex, region", conn)
print(df_customers.to_string())

print("\n💳 TRANSACTION FACT TABLE:")
df_trans = pd.read_sql_query("""
    SELECT COUNT(*) as total_transactions, 
           AVG(amount) as avg_amount,
           MIN(amount) as min_amount,
           MAX(amount) as max_amount
    FROM fact_transactions
""", conn)
print(df_trans.to_string())

conn.close()
print("\n" + "="*60)
