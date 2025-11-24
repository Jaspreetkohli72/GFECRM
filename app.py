import streamlit as st
import pandas as pd
from supabase import create_client, Client
import json
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Smart Home Business Estimator",
    page_icon="🏠",
    layout="wide",
)

# --- DATABASE CONNECTION ---

# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection() -> Client:
    """Initializes a connection to the Supabase database."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        st.stop()

supabase = init_connection()

# --- HELPER FUNCTIONS ---

def run_query(query, params=None):
    """Executes a query on the Supabase database."""
    try:
        if params:
            return supabase.table(query).select("*").execute()
        else:
            return supabase.from_(query).select("*").execute()
    except Exception as e:
        st.error(f"Error running query '{query}': {e}")
        return None

def get_clients():
    """Fetches all clients from the database."""
    return supabase.table("clients").select("*").order("id", desc=True).execute().data

def get_inventory():
    """Fetches all inventory items from the database."""
    return supabase.table("inventory").select("*").order("item_name").execute().data

def get_settings():
    """Fetches all settings from the database."""
    settings_data = supabase.table("settings").select("*").execute().data
    return {item['setting_name']: item['value'] for item in settings_data}

# --- UI TABS ---

st.title("🏠 Smart Home Business Estimator")

tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard & Active Clients",
    "New Client",
    "Estimator",
    "Inventory & Settings"
])

# --- TAB 1: DASHBOARD & ACTIVE CLIENTS ---
with tab1:
    st.header("Active Clients")
    clients = get_clients()

    if not clients:
        st.warning("No clients found. Add a new client to get started.")
    else:
        active_clients = [c for c in clients if c['status'] != 'Paid']
        if not active_clients:
            st.success("All clients are settled up! No active projects.")
        else:
            df_clients = pd.DataFrame(active_clients)[['name', 'status', 'phone', 'address', 'next_action_date']]
            st.dataframe(df_clients, use_container_width=True)

            for client in active_clients:
                with st.expander(f"{client['name']} - {client['status']}"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("Client Details")
                        st.write(f"**Phone:** {client['phone']}")
                        st.write(f"**Address:** {client['address']}")
                        st.write(f"**Location:** [Open Map]({client['gmaps_link']})")
                        if client['start_date']:
                            st.info(f"Work started on: {datetime.strptime(client['start_date'], '%Y-%m-%d').strftime('%d %b %Y')}")

                        st.subheader("Update Status")
                        if client['status'] == 'Active':
                            start_date = st.date_input("Select Work Start Date", key=f"date_{client['id']}")
                            if st.button("Mark Order Received", key=f"order_{client['id']}"):
                                supabase.table("clients").update({
                                    "status": "Order Received",
                                    "start_date": str(start_date)
                                }).eq("id", client['id']).execute()
                                st.success(f"Status for {client['name']} updated to 'Order Received'.")
                                st.rerun()

                        if client['status'] == 'Order Received':
                            if st.button("Mark Work Done", key=f"work_{client['id']}"):
                                supabase.table("clients").update({"status": "Work Done"}).eq("id", client['id']).execute()
                                st.success(f"Status for {client['name']} updated to 'Work Done'.")
                                st.rerun()

                        if client['status'] == 'Work Done':
                            with st.form(f"payment_form_{client['id']}"):
                                settlement = st.number_input("Final Settlement Amount (₹)", min_value=0.0, step=100.0, key=f"settle_{client['id']}")
                                submitted = st.form_submit_button("Mark as Paid & Archive")
                                if submitted:
                                    supabase.table("clients").update({
                                        "status": "Paid",
                                        "final_settlement_amount": settlement
                                    }).eq("id", client['id']).execute()
                                    st.success(f"Client {client['name']} marked as Paid and archived.")
                                    st.rerun()

                    with col2:
                        if client['internal_estimate'] and client['client_estimate']:
                            st.subheader("Internal Estimate")
                            internal_est = pd.DataFrame(client['internal_estimate'])
                            st.dataframe(internal_est, use_container_width=True)
                            total_profit = internal_est['Profit'].sum()
                            st.metric("Total Estimated Profit", f"₹{total_profit:,.2f}")


                            st.subheader("Client Estimate")
                            client_est = pd.DataFrame(client['client_estimate'])
                            st.dataframe(client_est, use_container_width=True)
                            total_client_cost = client_est['Final Rate'].sum()
                            st.metric("Total Client Cost", f"₹{total_client_cost:,.2f}")
                        else:
                            st.info("No estimate has been created for this client yet.")


# --- TAB 2: NEW CLIENT ---
with tab2:
    st.header("Create a New Client")
    with st.form("new_client_form"):
        name = st.text_input("Client Name*")
        phone = st.text_input("Phone Number")
        address = st.text_area("Site Address")
        gmaps = st.text_input("Google Maps Link or Lat/Long")

        submitted = st.form_submit_button("Create Client")
        if submitted:
            if not name:
                st.warning("Client Name is a required field.")
            else:
                try:
                    supabase.table("clients").insert({
                        "name": name,
                        "phone": phone,
                        "address": address,
                        "gmaps_link": gmaps
                    }).execute()
                    st.success(f"Client '{name}' created successfully!")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

# --- TAB 3: ESTIMATOR ---
with tab3:
    st.header("Create an Estimate")
    clients = get_clients()
    inventory = get_inventory()
    settings = get_settings()

    if not clients or not inventory:
        st.warning("Please add at least one client and one inventory item before using the estimator.")
    else:
        active_clients = [c for c in clients if c['status'] != 'Paid']
        client_options = {c['name']: c['id'] for c in active_clients}
        selected_client_name = st.selectbox("Select a Client", options=client_options.keys())

        st.subheader("Select Inventory Items")
        inventory_df = pd.DataFrame(inventory)
        inventory_df['Quantity'] = 0
        
        # Multiselect for items
        selected_items = st.multiselect(
            "Choose items for the estimate",
            options=inventory_df['item_name'].tolist()
        )
        
        estimate_items = []
        if selected_items:
            for item in selected_items:
                default_rate = inventory_df[inventory_df['item_name'] == item]['base_rate'].iloc[0]
                quantity = st.number_input(f"Quantity for {item} (Rate: ₹{default_rate})", min_value=1, step=1, key=item)
                estimate_items.append({"item_name": item, "quantity": quantity, "base_rate": float(default_rate)})

        if estimate_items:
            st.subheader("Estimate Calculation")
            
            part_margin = settings.get('part_margin_percent', 0) / 100
            labor_margin = settings.get('labor_margin_percent', 0) / 100
            extra_margin = settings.get('extra_margin_percent', 0) / 100

            internal_breakdown = []
            client_facing = []

            for item in estimate_items:
                base_cost = item['base_rate'] * item['quantity']
                part_profit = base_cost * part_margin
                labor_profit = base_cost * labor_margin
                extra_profit = base_cost * extra_margin
                total_profit = part_profit + labor_profit + extra_profit
                final_rate = base_cost + total_profit

                internal_breakdown.append({
                    "Item": item['item_name'],
                    "Qty": item['quantity'],
                    "Base Cost": base_cost,
                    "Part Profit": part_profit,
                    "Labor Profit": labor_profit,
                    "Extra Profit": extra_profit,
                    "Profit": total_profit,
                    "Final Rate": final_rate,
                })

                client_facing.append({
                    "Item": item['item_name'],
                    "Quantity": item['quantity'],
                    "Final Rate": final_rate,
                })

            st.subheader("Internal Estimate (With Profit Breakdown)")
            internal_df = pd.DataFrame(internal_breakdown)
            st.dataframe(internal_df, use_container_width=True)
            st.metric("Total Estimated Cost for Client", f"₹{internal_df['Final Rate'].sum():,.2f}")
            st.metric("Total Estimated Profit", f"₹{internal_df['Profit'].sum():,.2f}")

            st.subheader("Client-Facing Estimate")
            client_df = pd.DataFrame(client_facing)
            st.dataframe(client_df, use_container_width=True)

            if st.button("Save Estimate to Client"):
                client_id = client_options[selected_client_name]
                try:
                    supabase.table("clients").update({
                        "internal_estimate": json.dumps(internal_breakdown),
                        "client_estimate": json.dumps(client_facing),
                    }).eq("id", client_id).execute()
                    st.success(f"Estimate saved for {selected_client_name}!")
                except Exception as e:
                    st.error(f"Failed to save estimate: {e}")


# --- TAB 4: INVENTORY & SETTINGS ---
with tab4:
    st.header("Inventory Management")
    inventory = get_inventory()
    if inventory:
        inventory_df = pd.DataFrame(inventory).sort_values("id")
        edited_inventory = st.data_editor(
            inventory_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "item_name": "Item Name",
                "base_rate": st.column_config.NumberColumn(
                    "Base Rate (₹)",
                    min_value=0,
                    format="₹%.2f"
                )
            }
        )

        if st.button("Save Inventory Changes"):
            # This is a simplified save; for production, you'd need to handle updates, inserts, deletes separately.
            try:
                # Simple approach: delete all and re-insert. Not ideal for large datasets due to performance and ID changes.
                # A more robust solution would track changes row by row.
                supabase.table("inventory").delete().neq("id", -1).execute() # Delete all
                data_to_insert = edited_inventory.drop(columns=['id']).to_dict(orient='records')
                supabase.table("inventory").insert(data_to_insert).execute()
                st.success("Inventory updated successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Error updating inventory: {e}")

    st.divider()

    st.header("Global Profit Margins")
    settings = get_settings()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        part_margin = st.slider(
            "Parts Margin (%)", 
            min_value=0.0, max_value=100.0, 
            value=float(settings.get('part_margin_percent', 0)), 
            step=0.5
        )
    with col2:
        labor_margin = st.slider(
            "Labor Margin (%)", 
            min_value=0.0, max_value=100.0, 
            value=float(settings.get('labor_margin_percent', 0)), 
            step=0.5
        )
    with col3:
        extra_margin = st.slider(
            "Extra/Contingency Margin (%)", 
            min_value=0.0, max_value=100.0, 
            value=float(settings.get('extra_margin_percent', 0)), 
            step=0.5
        )
        
    if st.button("Save Global Margins"):
        try:
            supabase.table("settings").update({"value": part_margin}).eq("setting_name", "part_margin_percent").execute()
            supabase.table("settings").update({"value": labor_margin}).eq("setting_name", "labor_margin_percent").execute()
            supabase.table("settings").update({"value": extra_margin}).eq("setting_name", "extra_margin_percent").execute()
            st.success("Global margins updated!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to update settings: {e}")

st.sidebar.info("App developed by Gemini.")
st.sidebar.info("Remember to replace placeholder credentials in `.streamlit/secrets.toml`.")

# Add a placeholder for next_action_date to avoid key errors if the column doesn't exist in the fetched data
def get_clients():
    """Fetches all clients from the database and ensures 'next_action_date' exists."""
    data = supabase.table("clients").select("*").order("id", desc=True).execute().data
    for item in data:
        item.setdefault('next_action_date', None)  # Add default if key is missing
    return data
