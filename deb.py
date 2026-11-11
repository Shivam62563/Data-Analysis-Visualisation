import pandas as pd
import mysql.connector
import os

csv_files = [
    ('customers.csv', 'customers'),
    ('orders.csv', 'orders'),
    ('sellers.csv', 'sellers'),
    ('products.csv', 'products'),
    ('geolocation.csv', 'delivery'),
    ('payments.csv', 'payments'),
    ('order_items.csv', 'orderitems')
]

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='12@sshivam',
    database='ecommerce',
    port=3306,
    autocommit=False
)

cursor = conn.cursor()

folder_path = 'C:/Users/LENOVO/OneDrive/Documents/e-commerce'

def get_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        return 'DOUBLE'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATETIME'
    else:
        return 'VARCHAR(255)'

BATCH_SIZE = 500   # ⭐ KEY FIX ⭐

for csv_file, table_name in csv_files:
    file_path = os.path.join(folder_path, csv_file)
    print(f"\nProcessing {csv_file} → `{table_name}`")

    df = pd.read_csv(file_path)

    df.columns = [
        col.strip()
           .replace(' ', '_')
           .replace('-', '_')
           .replace('.', '_')
        for col in df.columns
    ]

    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass

    df = df.where(pd.notnull(df), None)

    columns_sql = ", ".join(
        f"`{col}` {get_sql_type(df[col].dtype)}"
        for col in df.columns
    )

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            {columns_sql}
        )
    """)

    insert_query = f"""
    INSERT INTO `{table_name}` (
        {', '.join(f'`{col}`' for col in df.columns)}
    ) VALUES (
        {', '.join(['%s'] * len(df.columns))}
    )
    """

    data = [
        tuple(None if pd.isna(x) else x for x in row)
        for row in df.to_numpy()
    ]

    # ✅ INSERT IN BATCHES
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        cursor.executemany(insert_query, batch)
        conn.commit()
        print(f"Inserted {i + len(batch)} / {len(data)} rows")

print("\n✅ All files imported successfully!")

cursor.close()
conn.close()
