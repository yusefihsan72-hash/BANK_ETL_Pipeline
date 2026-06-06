"""
Sample data generator for BANK_ETL_Pipeline
Generates realistic customer and transaction CSV files with larger datasets
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
NUM_CUSTOMERS = 1600  # Generate ~2700 customers when including transactions
NUM_TRANSACTIONS_PER_CUSTOMER = 20  # Multiple transactions per customer
OUTPUT_DIR = Path("data/incoming")

# Sample data pools
REGIONS = ["TOWN", "INNER_CITY", "RURAL", "SUBURBAN"]
DESCRIPTIONS = ["Interest", "Debit Card", "ATM Withdrawal", "Direct Deposit", "Transfer", "Payment", "Reversal", "Charge"]
GENDERS = ["MALE", "FEMALE"]

def generate_customers(num_customers: int, start_id: int = 13500) -> list:
    """Generate realistic customer data"""
    customers = []
    for i in range(num_customers):
        customer_id = f"ID{start_id + i}"
        age = random.randint(18, 75)
        sex = random.choice(GENDERS)
        region = random.choice(REGIONS)
        income = round(random.uniform(5000, 100000), 2) if random.random() > 0.15 else ""
        married = random.choice(["YES", "NO", ""])
        children = random.randint(0, 5) if random.random() > 0.3 else ""
        car = random.choice(["YES", "NO"])
        save_act = random.choice(["YES", "NO"])
        current_act = random.choice(["YES", "NO"])
        mortgage = random.choice(["YES", "NO", ""])
        pep = random.choice(["YES", "NO"])
        
        customers.append({
            "_id": customer_id,
            "age": age,
            "sex": sex,
            "region": region,
            "income": income,
            "married": married,
            "children": children,
            "car": car,
            "save_act": save_act,
            "current_act": current_act,
            "mortgage": mortgage,
            "pep": pep,
        })
    return customers

def generate_transactions(customers: list, transactions_per_customer: int = 20) -> list:
    """Generate realistic transaction data"""
    transactions = []
    base_date = datetime(2026, 4, 3)  # Today's date
    
    for customer in customers:
        customer_id = customer["_id"]
        for _ in range(transactions_per_customer):
            date = base_date - timedelta(days=random.randint(0, 90))
            description = random.choice(DESCRIPTIONS)
            
            if description == "Interest":
                deposits = round(random.uniform(10, 500), 2)
                withdrawals = 0.00
            elif description in ["Debit Card", "ATM Withdrawal", "Charge"]:
                deposits = 0.00
                withdrawals = round(random.uniform(10, 1000), 2)
            elif description == "Direct Deposit":
                deposits = round(random.uniform(500, 5000), 2)
                withdrawals = 0.00
            else:  # Transfer, Payment, Reversal
                if random.random() > 0.5:
                    deposits = round(random.uniform(100, 2000), 2)
                    withdrawals = 0.00
                else:
                    deposits = 0.00
                    withdrawals = round(random.uniform(50, 1500), 2)
            
            balance = round(random.uniform(1000, 100000), 2)
            
            transactions.append({
                "customer_id": customer_id,
                "Date": date.strftime("%d-%b-%Y"),
                "Description": description,
                "Deposits": f"{deposits:,.2f}",
                "Withdrawls": f"{withdrawals:,.2f}",
                "Balance": f"{balance:,.2f}",
            })
    
    return transactions

def save_customers_csv(customers: list, filename: str):
    """Save customers to CSV file"""
    output_path = OUTPUT_DIR / filename
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["_id", "age", "sex", "region", "income", "married", "children", 
                     "car", "save_act", "current_act", "mortgage", "pep"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(customers)
    
    print(f"✅ Created {output_path} with {len(customers)} customers")

def save_transactions_csv(transactions: list, filename: str):
    """Save transactions to CSV file"""
    output_path = OUTPUT_DIR / filename
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["customer_id", "Date", "Description", "Deposits", "Withdrawls", "Balance"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"✅ Created {output_path} with {len(transactions)} transactions")

if __name__ == "__main__":
    from datetime import datetime
    import time
    
    print("=" * 70)
    print("BANK ETL - Sample Data Generator (Batch 2)")
    print("=" * 70)
    
    # Use timestamp to generate unique filenames
    timestamp = datetime.now().strftime("%d%m%y")
    
    # Generate data
    print(f"\n📊 Generating {NUM_CUSTOMERS} customers...")
    customers = generate_customers(NUM_CUSTOMERS)
    
    print(f"💳 Generating {NUM_CUSTOMERS * NUM_TRANSACTIONS_PER_CUSTOMER} transactions...")
    transactions = generate_transactions(customers, NUM_TRANSACTIONS_PER_CUSTOMER)
    
    # Save to CSV files with unique names
    print("\n💾 Saving to CSV files in data/incoming/...")
    save_customers_csv(customers, f"{timestamp}_Customer.csv")
    save_transactions_csv(transactions, f"{timestamp}_Transactions.csv")
    
    print("\n" + "=" * 70)
    print("✨ Sample data ready! Files placed in data/incoming/")
    print("Pipeline will automatically process them.")
    print("=" * 70)
