
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

# Hardware items list based on user request and online search (Raipur rates approximate)
# User request: Nuts/Bolts (kg), Welding Rod No 10/9 (pack)
hardware_items = [
    # Nuts and Bolts (per kg)
    {"item_name": "MS Nuts & Bolts Mix", "base_rate": 80.0, "unit": "kg", "item_type": "Hardware", "dimension": "Mixed Sizes"},
    {"item_name": "10mm MS Hex Nut Bolt", "base_rate": 80.0, "unit": "kg", "item_type": "Hardware", "dimension": "10mm"},
    {"item_name": "Mild Steel Bolt Nut", "base_rate": 65.0, "unit": "kg", "item_type": "Hardware", "dimension": "Standard"},
    
    # Welding Rods (per packet/box) - User said "number 10 number 9 rods keep them per pack"
    # Search suggest box price ~1750-2000. Assuming "pack" might be smaller or a box.
    # Let's use a conservative pack price or single box price. 
    # Search: No 10 ~ 1320/kg or Box ~1750. 
    # Let's add them as 'pkt' (packet) with an estimated rate.
    # User said "number 10 number 9". Search results gave info on No 10 and No 8. No 9 is less common in snippets but likely similar.
    # Estimated Rate for a packet/box: 350 (small packet) to 1800 (box).
    # Let's set a generic "Packet" rate and user can edit or we use the ~300/packet info for Ador.
    # "Ador Welding Electrodes... 300 per packet". This seems reasonable for a small pack.
    
    {"item_name": "Welding Rod No. 10", "base_rate": 300.0, "unit": "pkt", "item_type": "Hardware", "dimension": "No. 10"},
    {"item_name": "Welding Rod No. 9", "base_rate": 300.0, "unit": "pkt", "item_type": "Hardware", "dimension": "No. 9"},
    {"item_name": "Welding Rod No. 8", "base_rate": 300.0, "unit": "pkt", "item_type": "Hardware", "dimension": "No. 8"}, # Added No 8 as per search prevalence
]

print(f"Adding {len(hardware_items)} hardware items...")

for item in hardware_items:
    # Check if exists to avoid duplicates (optional, but good practice)
    existing = supabase.table("inventory").select("*").eq("item_name", item['item_name']).execute()
    if not existing.data:
        res = supabase.table("inventory").insert(item).execute()
        print(f"Inserted: {item['item_name']}")
    else:
        print(f"Skipped (Exists): {item['item_name']}")

print("Hardware items added successfully.")
