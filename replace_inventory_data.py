
import csv
import toml
from supabase import create_client, Client
import sys
import os

# 1. Setup Supabase
try:
    # Try different paths for secrets
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        secrets_path = os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml")
        
    if not os.path.exists(secrets_path):
        # Fallback to local file in GFECRM if running from there
        secrets_path = "c:\\Users\\Jaspreet\\Documents\\GFECRM\\.streamlit\\secrets.toml"

    print(f"Loading secrets from: {secrets_path}")
    secrets = toml.load(secrets_path)
    url = secrets["SUPABASE_URL"]
    key = secrets["SUPABASE_KEY"]
    
    supabase: Client = create_client(url, key)
    print("Supabase connected.")

except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    sys.exit(1)

# 2. Read CSV Data
csv_path = "c:\\Users\\Jaspreet\\Documents\\GFECRM\\inventory_import.csv"
items_to_insert = []

try:
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Clean up boolean logic removed

            
            item = {
                "item_name": row['item_name'],
                "base_rate": float(row['base_rate']),
                "unit": row['unit'],
                "item_type": row['item_type'],
                "dimension": row['dimension']
            }
            items_to_insert.append(item)
    print(f"Loaded {len(items_to_insert)} items from CSV.")
except Exception as e:
    print(f"Error reading CSV: {e}")
    sys.exit(1)

# 3. Replace Data
if items_to_insert:
    try:
        print("Emptying existing inventory table...")
        # Delete all rows. id gt 0 covers all generated ids.
        supabase.table("inventory").delete().gt("id", 0).execute()
        
        print("Inserting new items...")
        # Batch insert to avoid payload limits if necessary, though 116 is small enough
        # But supabase-py sometimes has issues with large batches? 100 is safe.
        batch_size = 50
        for i in range(0, len(items_to_insert), batch_size):
            batch = items_to_insert[i:i + batch_size]
            supabase.table("inventory").insert(batch).execute()
            print(f"Inserted batch {i} to {i+len(batch)}")
            
        print("SUCCESS: Inventory replaced successfully.")
    except Exception as e:
        print(f"Error updating database: {e}")
else:
    print("No items found to insert.")
