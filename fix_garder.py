
import toml
from supabase import create_client, Client
import os

# Setup Supabase
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

# Fetch items with 'GARDER' in name or type
print("Fetching 'GARDER' items...")
response = supabase.table("inventory").select("*").ilike("item_type", "%GARDER%").execute()

items = response.data
print(f"Found {len(items)} items to update.")

count = 0
for item in items:
    new_type = item['item_type'].replace('GARDER', 'Garder')
    new_name = item['item_name'].replace('GARDER', 'Garder')
    
    if new_type != item['item_type'] or new_name != item['item_name']:
        supabase.table("inventory").update({
            "item_type": new_type,
            "item_name": new_name
        }).eq("id", item['id']).execute()
        count += 1
        print(f"Updated: {item['item_name']} -> {new_name}")

print(f"Successfully updated {count} items.")
