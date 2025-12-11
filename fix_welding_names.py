
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

# Refine Welding Rod Names
# "Welding rod of size No. 10" -> "Welding Rod No. 10"
# Or if it was still "No. 10", update it strictly.
# We will check for both current possibilities and set to target.

updates = {
    # If script ran successfully previously:
    "Welding rod of size No. 10": "Welding Rod No. 10",
    "Welding rod of size No. 9": "Welding Rod No. 9",
    "Welding rod of size No. 8": "Welding Rod No. 8",
    
    # If script failed or state is mixed:
    "No. 10": "Welding Rod No. 10",
    "No. 9": "Welding Rod No. 9",
    "No. 8": "Welding Rod No. 8"
}

print("Refining welding rod dimensions...")
count = 0

response = supabase.table("inventory").select("*").eq("item_type", "Hardware").eq("unit", "pkt").execute()
items = response.data

for item in items:
    current_dim = item['dimension']
    if current_dim in updates:
        new_dim = updates[current_dim]
        # Only update if different
        if new_dim != current_dim:
            supabase.table("inventory").update({"dimension": new_dim}).eq("id", item['id']).execute()
            print(f"Updated: {item['item_name']} ({current_dim}) -> {new_dim}")
            count += 1
    elif current_dim.startswith("Welding Rod No."):
        print(f"Skipped (Already correct): {current_dim}")

print(f"Successfully updated {count} items.")
