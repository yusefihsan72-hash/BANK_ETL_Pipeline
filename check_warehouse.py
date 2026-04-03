import sqlite3
import pandas as pd

# Connect to warehouse database
conn = sqlite3.connect('warehouse/bank_warehouse.db')

# Get all table names
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("=" * 80)
print("WAREHOUSE DATABASE - ALL TABLES")
print("=" * 80)
for table in tables:
    table_name = table[0]
    print(f"\n📊 Table: {table_name}")
    print("-" * 80)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        if len(df) > 0:
            print(f"Total Rows: {len(df)}")
            print(f"Columns: {list(df.columns)}\n")
            print(df.to_string())
        else:
            print("(Empty table)")
    except Exception as e:
        print(f"Error reading table: {e}")

conn.close()
print("\n" + "=" * 80)
