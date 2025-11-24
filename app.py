import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import time
from fpdf import FPDF
from streamlit_js_eval import get_geolocation
import extra_streamlit_components as stx

# ---------------------------
# 1. SETUP & CONNECTION
# ---------------------------
st.set_page_config(page_title="Jugnoo CRM", page_icon="🏗️", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 15px;
        border-radius: 8px;
        color: white;
    }
    [data-testid="stMetricLabel"] { color: #b4b4b4; }
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
# 2. AUTHENTICATION (COOKIES)
# ---------------------------
# IMPORTANT: Adding a key here helps persistence
@st.cache_resource(experimental_allow_widgets=True)
def get_manager():
    return stx.CookieManager(key="auth_cookie_manager")

cookie_manager = get_manager()

def check_login(username, password):
    try:
        res = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        return len(res.data) > 0
    except:
        return False

def login_section():
    st.title("🔒 Jugnoo CRM")
    
    # 1. Try to get cookie
    cookie_user = cookie_manager.get(cookie="jugnoo_user")
    
    # 2. If Cookie found, auto-login
    if cookie_user:
        st.session_state.logged_in = True
        st.session_state.username = cookie_user
        return 

    # 3. If already logged in via session state, skip
    if st.session_state.get('logged_in'):
        return

    # 4. Show Login Form
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("login"):
            st.subheader("Sign In")
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login", type="primary"):
                if check_login(user, pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    
                    # FIX: Correct Date Format for Cookie
                    expires = datetime.now() + timedelta(days=7)
                    cookie_manager.set("jugnoo_user", user, expires_at=expires)
                    
                    st.success("Login Successful!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
    st.stop()

# Run Login Check
login_section()

# ---------------------------
# 3. HELPER FUNCTIONS
# ---------------------------
def run_query(query_func):
    try:
        return query_func.execute()
    except Exception as e:
        return None

def get_settings():
    defaults = {"part_margin": 0.15, "labor_margin": 0.20, "extra_margin": 0.05, "daily_labor_cost": 1000.0}
    try:
        response = run_query(supabase.table("settings").select("*"))
        if response and response.data:
            db_data = response.data[0]
            return {k: db_data.get(k, v) for k, v in defaults.items()}
    except:
        pass
    return defaults

def create_pdf(client_name, items, labor_days, labor_total, grand_total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Jugnoo - Estimate", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Client: {client_name}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Item", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(60, 10, "Amount", 1)
    pdf.ln()
    pdf.set_font("Arial", '', 12)
    for item in items:
        pdf.cell(100, 10, str(item['Item']), 1)
        pdf.cell(30, 10, str(item['Qty']), 1)
        pdf.cell(60, 10, f"{item['Total Price']:.2f}", 1)
        pdf.ln()
    pdf.ln(5)
    pdf.cell(130, 10, f"Labor / Installation ({labor_days} Days)", 1)
    pdf.cell(60, 10, f"{labor_total:.2f}", 1)
    pdf.ln()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(130, 10, "Grand Total", 1)
    pdf.cell(60, 10, f"{grand_total:.2f}", 1)
    return pdf.output(dest='S').encode('latin-1')

# ---------------------------
# 4. MAIN APP UI
# ---------------------------
st.sidebar.write(f"👤 **{st.session_state.username}**")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    cookie_manager.delete("jugnoo_user")
    st.rerun()

if not supabase: st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📋 Dashboard", "➕ New Client", "🧮 Estimator", "⚙️ Settings"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("Active Projects")
    response = run_query(supabase.table("clients").select("*").order("created_at", desc=True))
    
    if response and response.data:
        df = pd.DataFrame(response.data)
        cols_show = ['name', 'status', 'start_date', 'phone', 'address']
        valid_cols = [c for c in cols_show if c in df.columns]
        st.dataframe(df[valid_cols], use_container_width=True, hide_index=True)
        
        st.divider()
        
        client_map = {c['name']: c for c in response.data}
        selected_client_name = st.selectbox("Select Client to Manage", list(client_map.keys()), index=None, key="dash_select")
        
        if selected_client_name:
            client = client_map[selected_client_name]
            
            st.markdown("### 🛠️ Manage Client")
            col_details, col_status = st.columns([1.5, 1])
            
            with col_details:
                st.write("**Edit Details**")
                
                # GPS Button for Dashboard (Visible Toggle)
                if st.toggle("Show GPS Button", key="tgl_dash"):
                    gps_dash = get_geolocation(component_key=f"gps_{client['id']}")
                    if gps_dash:
                        lat_d = gps_dash['coords']['latitude']
                        long_d = gps_dash['coords']['longitude']
                        st.session_state[f"loc_{client['id']}"] = f"http://googleusercontent.com/maps.google.com/?q={lat_d},{long_d}"
                        st.info("Location received! Check the Maps Link field below.")

                with st.form("edit_client_details"):
                    new_name = st.text_input("Name", value=client['name'])
                    new_phone = st.text_input("Phone", value=client.get('phone', ''))
                    new_addr = st.text_area("Address", value=client.get('address', ''))
                    
                    current_loc = st.session_state.get(f"loc_{client['id']}", client.get('location', ''))
                    new_loc = st.text_input("Maps Link", value=current_loc)
                    
                    if st.form_submit_button("💾 Save Changes"):
                        run_query(supabase.table("clients").update({
                            "name": new_name, "phone": new_phone, "address": new_addr, "location": new_loc
                        }).eq("id", client['id']))
                        st.success("Details Updated!")
                        time.sleep(0.5)
                        st.rerun()

            with col_status:
                st.write("**Project Status**")
                status_options = ["Estimate Given", "Order Received", "Work In Progress", "Work Done", "Closed"]
                try:
                    curr_idx = status_options.index(client.get('status'))
                except:
                    curr_idx = 0
                
                new_status = st.selectbox("Update Status", status_options, index=curr_idx, key=f"st_{client['id']}")
                
                start_date_val = None
                if new_status in ["Order Received", "Work In Progress", "Work Done"]:
                    current_date_str = client.get('start_date')
                    if current_date_str:
                        default_date = datetime.strptime(current_date_str, '%Y-%m-%d').date()
                    else:
                        default_date = datetime.now().date()
                    start_date_val = st.date_input("📅 Start Date", value=default_date)

                if st.button("Update Status", key=f"btn_st_{client['id']}"):
                    updates = {"status": new_status}
                    if start_date_val:
                        updates["start_date"] = start_date_val.isoformat()
                        
                    run_query(supabase.table("clients").update(updates).eq("id", client['id']))
                    st.success("Status Updated!")
                    time.sleep(0.5)
                    st.rerun()

            if client.get('internal_estimate'):
                st.divider()
                st.subheader("📄 Saved Estimate")
                est_data = client['internal_estimate']
                if isinstance(est_data, dict):
                    items_df = pd.DataFrame(est_data.get('items', []))
                else:
                    items_df = pd.DataFrame(est_data) if isinstance(est_data, list) else pd.DataFrame()

                if not items_df.empty:
                    if "Total Price" in items_df.columns:
                        st.dataframe(items_df, use_container_width=True)
                        st.metric("Total Quoted", f"₹{items_df['Total Price'].sum():,.2f}")

# --- TAB 2: NEW CLIENT ---
with tab2:
    st.subheader("Add New Client")
    
    # GPS Button for New Client (Visible Toggle)
    if st.toggle("📍 Get Current Location", key="tgl_new"):
        loc_button = get_geolocation(component_key="gps_btn_new")
        if loc_button:
            lat = loc_button['coords']['latitude']
            long = loc_button['coords']['longitude']
            st.session_state['new_loc_val'] = f"http://googleusercontent.com/maps.google.com/?q={lat},{long}"
            st.success("Location Captured! See field below.")

    with st.form("add_client_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Client Name")
        phone = c2.text_input("Phone Number")
        address = st.text_area("Address")
        
        default_loc = st.session_state.get('new_loc_val', "")
        loc = st.text_input("Google Maps Link", value=default_loc)
        
        if st.form_submit_button("Create Client", type="primary"):
            run_query(supabase.table("clients").insert({
                "name": name, "phone": phone, "address": address, "location": loc,
                "status": "Estimate Given", "created_at": datetime.now().isoformat()
            }))
            st.success(f"Client {name} Added!")
            if 'new_loc_val' in st.session_state: del st.session_state['new_loc_val']
            time.sleep(1)
            st.rerun()

# --- TAB 3: ESTIMATOR ---
with tab3:
    st.subheader("Estimator Engine")
    all_clients = run_query(supabase.table("clients").select("id, name, internal_estimate").neq("status", "Closed"))
    client_dict = {c['name']: c for c in all_clients.data} if all_clients and all_clients.data else {}
    target_client_name = st.selectbox("Select Client", list(client_dict.keys()), key="est_sel")
    
    if target_client_name:
        target_client = client_dict[target_client_name]
        saved_est = target_client.get('internal_estimate')
        loaded_items = []
        saved_margins = None
        saved_days = 1.0
        
        if isinstance(saved_est, dict):
            loaded_items = saved_est.get('items', [])
            saved_margins = saved_est.get('margins')
            saved_days = saved_est.get('days', 1.0)
        elif isinstance(saved_est, list):
            loaded_items = saved_est
            
        ss_key = f"est_items_{target_client['id']}"
        if ss_key not in st.session_state: st.session_state[ss_key] = loaded_items

        st.divider()
        global_settings = get_settings()
        use_custom = st.checkbox("🛠️ Use Custom Margins", value=(saved_margins is not None), key="cust_check")
        
        if use_custom:
            def_p = int((saved_margins['p'] if saved_margins else global_settings['part_margin']) * 100)
            def_l = int((saved_margins['l'] if saved_margins else global_settings['labor_margin']) * 100)
            def_e = int((saved_margins['e'] if saved_margins else global_settings['extra_margin']) * 100)
            mc1, mc2, mc3 = st.columns(3)
            cust_p = mc1.slider("Part %", 0, 100, def_p, key="cp") / 100
            cust_l = mc2.slider("Labor %", 0, 100, def_l, key="cl") / 100
            cust_e = mc3.slider("Extra %", 0, 100, def_e, key="ce") / 100
            active_margins = {'part_margin': cust_p, 'labor_margin': cust_l, 'extra_margin': cust_e}
        else:
            active_margins = global_settings
            
        days_to_complete = st.slider("⏳ Days to Complete", 0.5, 30.0, float(saved_days), 0.5)

        st.divider()
        inv_data = run_query(supabase.table("inventory").select("*"))
        if inv_data and inv_data.data:
            inv_map = {i['item_name']: i['base_rate'] for i in inv_data.data}
            with st.form("add_item_est", clear_on_submit=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                item_name = c1.selectbox("Select Item", list(inv_map.keys()))
                qty = c2.number_input("Quantity", min_value=1.0, step=0.5)
                if st.form_submit_button("⬇️ Add"):
                    st.session_state[ss_key].append({"Item": item_name, "Qty": qty, "Base Rate": inv_map[item_name]})
                    st.rerun()
