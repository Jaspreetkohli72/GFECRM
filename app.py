import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# ---------------------------
# 1. SETUP & CONNECTION
# ---------------------------
st.set_page_config(page_title="Jugnoo CRM", page_icon="🏗️", layout="wide")

# CSS to hide Streamlit footer and cleaner look
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ---------------------------
# 2. HELPER FUNCTIONS
# ---------------------------
def run_query(query_func):
    try:
        return query_func.execute()
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

def get_settings():
    response = run_query(supabase.table("settings").select("*"))
    if response and response.data:
        return response.data[0]
    return {"part_margin": 0.15, "labor_margin": 0.20, "extra_margin": 0.05}

# ---------------------------
# 3. UI TABS
# ---------------------------
st.title("🏗️ Jugnoo CRM")
tab1, tab2, tab3, tab4 = st.tabs(["📋 Dashboard", "➕ New Client", "🧮 Smart Estimator", "⚙️ Inventory"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Active Projects")
    response = run_query(supabase.table("clients").select("*").order("created_at", desc=True))
    
    if response and response.data:
        # Prepare Data for Display
        df = pd.DataFrame(response.data)
        
        # Display Summary
        display_cols = ['name', 'status', 'phone', 'address']
        # Handle optional columns safely
        if 'next_action_date' in df.columns: display_cols.append('next_action_date')
        
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("Client Details & Actions")
        
        # Client Selector
        client_opts = {row['name']: row for row in response.data}
        selected_client_name = st.selectbox("Select Client to Manage", list(client_opts.keys()), index=None)
        
        if selected_client_name:
            client = client_opts[selected_client_name]
            
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**Current Status:** {client['status']}")
                st.write(f"📞 {client['phone']}")
                st.write(f"📍 {client['address']}")
                if client.get('location'):
                    st.markdown(f"[Open in Maps]({client['location']})")
            
            with c2:
                # Status Update
                st.write("**Update Status**")
                status_options = ["Estimate Given", "Order Received", "Work In Progress", "Work Done", "Closed"]
                
                # Find current index safely
                try:
                    curr_idx = status_options.index(client['status'])
                except:
                    curr_idx = 0
                    
                new_status = st.selectbox("Change Status", status_options, index=curr_idx, key=f"status_{client['id']}")
                if new_status != client['status']:
                    if st.button("Update Status", key="btn_update"):
                        run_query(supabase.table("clients").update({"status": new_status}).eq("id", client['id']))
                        st.success("Updated!")
                        st.rerun()

            # --- VIEW SAVED ESTIMATE (FIXED ERROR HERE) ---
            st.divider()
            st.write("### Saved Estimate")
            
            # Check if internal_estimate is not None and is a list/dict
            est_data = client.get('internal_estimate')
            
            if est_data and isinstance(est_data, list) and len(est_data) > 0:
                try:
                    saved_df = pd.DataFrame(est_data)
                    st.dataframe(saved_df, use_container_width=True)
                    
                    # Calculate Total
                    if 'Total (Internal)' in saved_df.columns:
                        total_profit = saved_df['Total (Internal)'].sum() - (saved_df['Base Rate'] * saved_df['Qty']).sum()
                        st.metric("Projected Profit", f"₹{total_profit:,.2f}")
                except Exception as e:
                    st.warning("Could not load estimate details (Data format issue).")
            else:
                st.info("No estimate saved for this client yet.")

# --- TAB 2: NEW CLIENT ---
with tab2:
    st.subheader("Add New Client")
    with st.form("new_client"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        phone = c2.text_input("Phone")
        address = st.text_area("Address")
        loc = st.text_input("Maps Link")
        
        if st.form_submit_button("Create Client"):
            run_query(supabase.table("clients").insert({
                "name": name, "phone": phone, "address": address, "location": loc, 
                "status": "Estimate Given", "created_at": datetime.now().isoformat()
            }))
            st.success("Added!")

# --- TAB 3: SMART ESTIMATOR ---
with tab3:
    st.subheader("Create Estimate")
    
    # 1. Select Client
    clients = run_query(supabase.table("clients").select("id, name").neq("status", "Closed"))
    if clients.data:
        client_map = {c['name']: c['id'] for c in clients.data}
        target_client = st.selectbox("Select Client", list(client_map.keys()))
        
        if target_client:
            st.divider()
            
            # 2. Get Data needed for calculation
            settings = get_settings()
            inventory_resp = run_query(supabase.table("inventory").select("item_name, base_rate"))
            
            if inventory_resp.data:
                inv_df = pd.DataFrame(inventory_resp.data)
                item_list = inv_df['item_name'].tolist()
                
                # 3. FAST ENTRY TABLE (Data Editor)
                st.info("👇 Add items below. Select Item from the dropdown and type Quantity.")
                
                # Initialize session state for the editor if needed
                if "editor_rows" not in st.session_state:
                    st.session_state.editor_rows = [{"Item": None, "Qty": 1}]

                edited_df = st.data_editor(
                    st.session_state.editor_rows,
                    num_rows="dynamic",
                    column_config={
                        "Item": st.column_config.SelectboxColumn(
                            "Item Name",
                            help="Select item from inventory",
                            width="medium",
                            options=item_list,
                            required=True
                        ),
                        "Qty": st.column_config.NumberColumn(
                            "Quantity",
                            min_value=0.5,
                            step=0.5,
                            required=True
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )

                # 4. LIVE CALCULATION
                if not pd.DataFrame(edited_df).empty:
                    # Filter out empty rows
                    valid_rows = [r for r in edited_df if r["Item"] is not None]
                    
                    if valid_rows:
                        calc_df = pd.DataFrame(valid_rows)
                        
                        # Merge with base rates
                        calc_df = calc_df.merge(inv_df, left_on="Item", right_on="item_name", how="left")
                        
                        # Apply Margins
                        p_marg = settings['part_margin']
                        l_marg = settings['labor_margin']
                        e_marg = settings['extra_margin']
                        
                        # Internal Cost (With Profit Breakdown)
                        calc_df['Base Rate'] = calc_df['base_rate']
                        calc_df['Internal Rate'] = calc_df['Base Rate'] * (1 + p_marg + l_marg + e_marg)
                        calc_df['Total (Internal)'] = calc_df['Internal Rate'] * calc_df['Qty']
                        
                        # Client Rate (Rounded/Clean)
                        calc_df['Client Rate'] = calc_df['Internal Rate'] # Can add extra buffer if needed
                        calc_df['Total (Client)'] = calc_df['Client Rate'] * calc_df['Qty']
                        
                        # Show Results
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write("### 🔒 Internal View (For You)")
                            st.dataframe(calc_df[['Item', 'Qty', 'Base Rate', 'Total (Internal)']], hide_index=True)
                            my_profit = calc_df['Total (Internal)'].sum() - (calc_df['Base Rate'] * calc_df['Qty']).sum()
                            st.success(f"💰 Your Profit: ₹{my_profit:,.2f}")
                            
                        with c2:
                            st.write("### 📄 Client View")
                            client_view = calc_df[['Item', 'Qty', 'Client Rate', 'Total (Client)']]
                            st.dataframe(client_view, hide_index=True)
                            st.metric("Client Total", f"₹{client_view['Total (Client)'].sum():,.2f}")
                            
                        # Save Button
                        if st.button("💾 Save Estimate to Client Profile", type="primary"):
                            # Convert to JSON serializable format
                            json_data = calc_df[['Item', 'Qty', 'Base Rate', 'Internal Rate', 'Total (Internal)']].to_dict(orient='records')
                            
                            run_query(supabase.table("clients").update({
                                "internal_estimate": json_data
                            }).eq("id", client_map[target_client]))
                            
                            st.balloons()
                            st.toast("Estimate Saved Successfully!")

# --- TAB 4: SETTINGS & INVENTORY ---
with tab4:
    st.subheader("Inventory Management")
    inv_resp = run_query(supabase.table("inventory").select("*").order("item_name"))
    
    if inv_resp and inv_resp.data:
        current_inv = pd.DataFrame(inv_resp.data)
        
        # We use a trick: Edit locally, but for Supabase usually we delete/insert or update rows.
        # For simplicity in this free version: We just allow adding new items via a form, 
        # and editing existing rates via a smaller editor.
        
        st.write("**Edit Base Rates**")
        updated_inv = st.data_editor(current_inv, num_rows="dynamic", key="inv_editor")
        
        # Note: True syncing of deleted rows requires more logic. 
        # This button simply upserts (adds/updates) modified rows.
        if st.button("Sync Inventory Changes"):
            # Convert DF to list of dicts
            records = updated_inv.to_dict(orient='records')
            # Upsert into Supabase
            for row in records:
                # If ID exists, it updates. If new (no ID), might fail without proper setup.
                # Safer: Insert new items via form below, Update rates here.
                if row.get('id'):
                    run_query(supabase.table("inventory").update({
                        "item_name": row['item_name'], 
                        "base_rate": row['base_rate']
                    }).eq("id", row['id']))
            st.success("Inventory Rates Updated!")

    st.divider()
    st.write("**Global Margins**")
    with st.form("margins"):
        s = get_settings()
        c1, c2, c3 = st.columns(3)
        p = c1.number_input("Part Margin", value=s['part_margin'], step=0.01)
        l = c2.number_input("Labor Margin", value=s['labor_margin'], step=0.01)
        e = c3.number_input("Extra Margin", value=s['extra_margin'], step=0.01)
        if st.form_submit_button("Update Margins"):
            run_query(supabase.table("settings").update({
                "part_margin": p, "labor_margin": l, "extra_margin": e
            }).eq("id", 1))
            st.success("Margins Saved")