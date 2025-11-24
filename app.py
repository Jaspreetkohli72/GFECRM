import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# ---------------------------
# 1. SETUP & CONNECTION
# ---------------------------
st.set_page_config(page_title="Jugnoo CRM", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stMetric {background-color: #f0f2f6; padding: 10px; border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource(ttl="1h")
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = init_connection()

# ---------------------------
# 2. HELPER FUNCTIONS
# ---------------------------
def run_query(query_func):
    try:
        return query_func.execute()
    except Exception as e:
        return None

def get_settings():
    defaults = {"part_margin": 0.15, "labor_margin": 0.20, "extra_margin": 0.05}
    try:
        response = run_query(supabase.table("settings").select("*"))
        if response and response.data:
            db_data = response.data[0]
            return {k: db_data.get(k, v) for k, v in defaults.items()}
    except:
        pass
    return defaults

# ---------------------------
# 3. UI TABS
# ---------------------------
st.title("🏗️ Jugnoo CRM")

if not supabase:
    st.error("Connection Error. Check Secrets.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📋 Dashboard", "➕ New Client", "🧮 Estimator", "⚙️ Inventory & Settings"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Active Projects")
    response = run_query(supabase.table("clients").select("*").order("created_at", desc=True))
    
    if response and response.data:
        df = pd.DataFrame(response.data)
        display_cols = [c for c in ['name', 'status', 'phone', 'address'] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True, hide_index=True)
        
        st.divider()
        
        client_map = {c['name']: c for c in response.data}
        selected_client_name = st.selectbox("Select Client to Manage", list(client_map.keys()), index=None)
        
        if selected_client_name:
            client = client_map[selected_client_name]
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**Status:** {client['status']}")
                st.write(f"📞 {client['phone']}")
                if client.get('location'):
                    st.markdown(f"📍 [View Map]({client['location']})")
            
            with c2:
                new_status = st.selectbox("Update Status", 
                    ["Estimate Given", "Order Received", "Work In Progress", "Work Done", "Closed"],
                    key=f"status_{client['id']}"
                )
                if st.button("Update Status", key=f"btn_{client['id']}"):
                    run_query(supabase.table("clients").update({"status": new_status}).eq("id", client['id']))
                    st.success("Updated!")
                    st.rerun()

# --- TAB 2: NEW CLIENT ---
with tab2:
    st.subheader("Add New Client")
    with st.form("add_client"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Client Name")
        phone = c2.text_input("Phone")
        address = st.text_area("Address")
        loc = st.text_input("Google Maps Link")
        
        if st.form_submit_button("Save Client", type="primary"):
            run_query(supabase.table("clients").insert({
                "name": name, "phone": phone, "address": address, "location": loc,
                "status": "Estimate Given", "created_at": datetime.now().isoformat()
            }))
            st.success("Client Added!")

# --- TAB 3: ESTIMATOR (CUSTOM MARGINS ADDED) ---
with tab3:
    st.subheader("Estimator Engine")
    
    # 1. Select Client
    all_clients = run_query(supabase.table("clients").select("id, name, internal_estimate").neq("status", "Closed"))
    client_dict = {c['name']: c for c in all_clients.data} if all_clients and all_clients.data else {}
    
    target_client_name = st.selectbox("Select Client", list(client_dict.keys()))
    
    if target_client_name:
        target_client = client_dict[target_client_name]
        
        # Load Saved Data
        saved_est = target_client.get('internal_estimate')
        # Handle case where saved data is just a list (old version) vs dict (new version with margins)
        loaded_items = []
        saved_margins = None
        
        if isinstance(saved_est, dict):
            loaded_items = saved_est.get('items', [])
            saved_margins = saved_est.get('margins')
        elif isinstance(saved_est, list):
            loaded_items = saved_est
            
        ss_key = f"est_items_{target_client['id']}"
        if ss_key not in st.session_state:
            st.session_state[ss_key] = loaded_items

        st.divider()
        
        # --- CUSTOM MARGIN LOGIC ---
        global_settings = get_settings()
        
        use_custom = st.checkbox("🛠️ Use Custom Margins for this Client", value=(saved_margins is not None))
        
        if use_custom:
            # Initialize with saved margins OR global defaults
            def_p = int((saved_margins['p'] if saved_margins else global_settings['part_margin']) * 100)
            def_l = int((saved_margins['l'] if saved_margins else global_settings['labor_margin']) * 100)
            def_e = int((saved_margins['e'] if saved_margins else global_settings['extra_margin']) * 100)
            
            mc1, mc2, mc3 = st.columns(3)
            cust_p = mc1.slider("Custom Part %", 0, 100, def_p, key="cp") / 100
            cust_l = mc2.slider("Custom Labor %", 0, 100, def_l, key="cl") / 100
            cust_e = mc3.slider("Custom Extra %", 0, 100, def_e, key="ce") / 100
            
            active_margins = {'part_margin': cust_p, 'labor_margin': cust_l, 'extra_margin': cust_e}
        else:
            active_margins = global_settings

        st.divider()

        # 3. Add Item Form
        inv_data = run_query(supabase.table("inventory").select("*"))
        if inv_data and inv_data.data:
            inv_map = {i['item_name']: i['base_rate'] for i in inv_data.data}
            
            with st.form("add_item_form", clear_on_submit=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                item_name = c1.selectbox("Select Item", list(inv_map.keys()))
                qty = c2.number_input("Quantity", min_value=1.0, step=0.5)
                
                if st.form_submit_button("⬇️ Add to List"):
                    st.session_state[ss_key].append({
                        "Item": item_name, "Qty": qty, "Base Rate": inv_map[item_name]
                    })
                    st.rerun()

        # 4. Editable List & Calculation
        if st.session_state[ss_key]:
            # Prepare calculation
            margin_mult = 1 + active_margins['part_margin'] + active_margins['labor_margin'] + active_margins['extra_margin']
            
            df = pd.DataFrame(st.session_state[ss_key])
            if "Qty" not in df.columns: df["Qty"] = 1.0
            if "Base Rate" not in df.columns: df["Base Rate"] = 0.0
            
            # Calculate Live
            df["Unit Price (Calc)"] = df["Base Rate"] * margin_mult
            df["Total Price"] = df["Unit Price (Calc)"] * df["Qty"]
            
            st.write("#### Estimate Items")
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                column_config={
                    "Item": st.column_config.TextColumn(disabled=True),
                    "Base Rate": st.column_config.NumberColumn(disabled=True, format="₹%.2f"),
                    "Unit Price (Calc)": st.column_config.NumberColumn(disabled=True, format="₹%.2f"),
                    "Total Price": st.column_config.NumberColumn(disabled=True, format="₹%.2f"),
                    "Qty": st.column_config.NumberColumn(min_value=0.1, step=0.5)
                },
                use_container_width=True,
                key=f"edit_{target_client['id']}"
            )
            
            # Sync edits
            current_items = edited_df.to_dict(orient="records")
            
            # Totals
            total_client = edited_df["Total Price"].sum()
            total_base = (edited_df["Base Rate"] * edited_df["Qty"]).sum()
            profit = total_client - total_base
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Base Cost", f"₹{total_base:,.0f}")
            c2.metric("Client Quote", f"₹{total_client:,.0f}")
            c3.metric("Projected Profit", f"₹{profit:,.0f}", delta="Profit")
            
            if st.button("💾 Save Estimate", type="primary"):
                # Prepare save object
                save_obj = {
                    "items": current_items,
                    "margins": {
                        'p': active_margins['part_margin'],
                        'l': active_margins['labor_margin'],
                        'e': active_margins['extra_margin']
                    } if use_custom else None
                }
                
                run_query(supabase.table("clients").update({
                    "internal_estimate": save_obj
                }).eq("id", target_client['id']))
                st.toast("Estimate Saved!", icon="✅")

# --- TAB 4: SETTINGS (SINGLE ROW SLIDERS) ---
with tab4:
    st.subheader("Global Profit Settings")
    s = get_settings()
    
    with st.form("margin_settings"):
        st.write("Defaults for new estimates (0-100%)")
        
        # SINGLE ROW - 3 COLUMNS
        c1, c2, c3 = st.columns(3)
        
        p_val = int(s.get('part_margin', 0.15) * 100)
        l_val = int(s.get('labor_margin', 0.20) * 100)
        e_val = int(s.get('extra_margin', 0.05) * 100)
        
        p = c1.slider("Part Margin %", 0, 100, p_val)
        l = c2.slider("Labor Margin %", 0, 100, l_val)
        e = c3.slider("Extra Margin %", 0, 100, e_val)
        
        st.info(f"Total Markup Applied: {p+l+e}%")
        
        if st.form_submit_button("Update Global Defaults"):
            run_query(supabase.table("settings").upsert({
                "id": 1, 
                "part_margin": p / 100.0, 
                "labor_margin": l / 100.0, 
                "extra_margin": e / 100.0
            }))
            st.success("Settings Saved!")
            st.cache_resource.clear()

    st.divider()
    st.subheader("Inventory")
    
    with st.form("inv_add"):
        c1, c2 = st.columns([2, 1])
        new_item = c1.text_input("Item Name")
        rate = c2.number_input("Base Rate", min_value=0.0)
        if st.form_submit_button("Add Item"):
            run_query(supabase.table("inventory").insert({"item_name": new_item, "base_rate": rate}))
            st.success("Added")
            st.rerun()
            
    inv = run_query(supabase.table("inventory").select("*").order("item_name"))
    if inv and inv.data:
        st.dataframe(pd.DataFrame(inv.data), use_container_width=True)
