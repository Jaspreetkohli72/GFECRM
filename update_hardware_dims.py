
import toml
from supabase import create_client, Client
import os

# Setup Supabase
secrets_path = ".streamlit/secrets.toml"
if not os.path.exists(secrets_path):
    secrets_path = os.path.join(os.path.expanduser("~"), ".streamlit", "secrets.toml")
    
if not os.path.exists(secrets_path):
    secrets_path = "c:\\Users\\Jaspreet\\Documents\\GFECRM\\.streamlit\\secrets.toml"

print(f"Loading secrets from: {secrets_path}")
secrets = toml.load(secrets_path)
url = secrets["SUPABASE_URL"]
key = secrets["SUPABASE_KEY"]

supabase: Client = create_client(url, key)

# Updates map: { current_dimension: new_dimension }
# Only for Nuts/Bolts items (Unit: kg)
updates = {
    "10mm": "Nuts and Bolts of size 10mm",
    "Mixed Sizes": "Nuts and Bolts Mixed Sizes",
    "Standard": "Nuts and Bolts Standard Size"
}

print("Updating hardware dimensions...")
count = 0

# Fetch all Hardware items with unit 'kg' (Nuts/Bolts)
response = supabase.table("inventory").select("*").eq("item_type", "Hardware").eq("unit", "kg").execute()
items = response.data

for item in items:
    current_dim = item['dimension']
    if current_dim in updates:
        new_dim = updates[current_dim]
        supabase.table("inventory").update({"dimension": new_dim}).eq("id", item['id']).execute()
        print(f"Updated: {item['item_name']} ({current_dim}) -> {new_dim}")
        count += 1

print(f"Successfully updated {count} items.")
