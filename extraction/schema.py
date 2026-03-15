# extraction/schema.py

# Real column name in the Customer CSV is '_id', not 'customer_id'
CUSTOMER_COLUMNS = [
    "_id", "age", "sex", "region", "income", "married",
    "children", "car", "save_act", "current_act", "mortgage", "pep",
]

# Real columns in the Transactions CSV
TRANSACTION_COLUMNS = [
    "customer_id", "Date", "Description", "Deposits", "Withdrawls", "Balance",
]

FILE_PATTERNS = {
    "customer": r'^\d{6}_Customer\.csv$',
    "transaction": r'^\d{6}_Transactions\.csv$',
}