import streamlit as st
from supabase import create_client
from utils import helpers
from utils.helpers import create_pdf

from datetime import datetime, timedelta
import time
import pandas as pd
import math
import textwrap


import altair as alt
import plotly.graph_objects as go
import extra_streamlit_components as stx
import streamlit.components.v1 as components
import html
import hmac
import hashlib


# ---------------------------
# 1. SETUP & CONNECTION
# ---------------------------
st.set_page_config(page_title="Galaxy CRM", page_icon="🏗️", layout="wide")

# === START OF CRITICAL CACHE FIX ===
if st.session_state.get('cache_fix_needed', True):
    st.cache_resource.clear()
    st.session_state.cache_fix_needed = False
# === END OF CRITICAL CACHE FIX ===

# --- HIDE STREAMLIT ANCHORS & TOOLBAR ---
st.markdown("""
    <style>
    /* Hide the link icon next to headers */
    [data-testid="stHeader"] a {
        display: none;
    }
    /* Hide Streamlit Header and Toolbar */
    [data-testid="stHeader"] {
        visibility: hidden;
    }
    [data-testid="stToolbar"] {
        visibility: hidden;
    }
    /* Reduce top spacing */
    .block-container {
        padding-top: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

st.markdown("""
    <style>
    /* System Fonts for Emoji Support */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
    }
    
    /* Deep Space Background */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
        color: #e2e8f0;
    }
    
    /* Glassmorphism Cards (With Border) */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: none !important;
        -webkit-text-fill-color: initial !important;
    }

    /* DataFrame & Tables - Match UI */
    div.stDataFrame {
        background-color: transparent !important;
        border: none !important;
    }
    
    [data-testid="stDataFrame"] div[class*="stDataFrame"] {
        background-color: transparent !important;
    }
    
    /* Premium Slate Buttons CSS Removed to normalize styling */

    
    <!-- Fix for mobile safe areas and browser chrome -->
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="theme-color" content="#0E1117">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-capable" content="yes">
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
# 2. CACHED DATA FUNCTIONS
# ---------------------------
@st.cache_data(ttl=60)
def get_clients():
    return supabase.table("clients").select("*").order("created_at", desc=True).execute()

@st.cache_data(ttl=300)
def get_inventory():
    return supabase.table("inventory").select("*").order("item_name").execute()

@st.cache_data(ttl=300)
def get_suppliers():
    return supabase.table("suppliers").select("*").order("name").execute()

@st.cache_data(ttl=300)
def get_staff():
    try:
        return supabase.table("staff").select("*").order("name").execute()
    except: return None

@st.cache_data(ttl=300)
def get_staff_roles():
    try:
        return supabase.table("staff_roles").select("*").execute()
    except: return None

@st.cache_data(ttl=60)
def get_projects():
    # Fetch projects with client name
    return supabase.table("projects").select("*, clients(name)").order("created_at", desc=True).execute()

@st.cache_data(ttl=300)
def get_project_types():
    return supabase.table("project_types").select("*").order("type_name").execute()

def fetch_clients_page(page, page_size, search_term=""):
    try:
        query = supabase.table("clients").select("*", count="exact")
        if search_term:
            query = query.ilike("name", f"%{search_term}%")
        
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        res = query.order("created_at", desc=True).range(start, end).execute()
        return res.data, res.count
    except Exception as e:
        st.error(f"Error fetching clients: {e}")
        return [], 0

def fetch_projects_page(page, page_size, search_term="", status_filter="All"):
    try:
        # Note: Search on joined tables is tricky in simple query.
        # We will search Project Type Name or Client Name if possible, 
        # but for V1 we might limit search to Project status or simplistic fields or post-filter if not effectively supported by simple API.
        # However, improved Supabase allows filtering on foreign tables.
        
        query = supabase.table("projects").select("*, clients!inner(name)", count="exact")
        
        if search_term:
             # Searching client name via the joined table
             query = query.ilike("clients.name", f"%{search_term}%")
        
        if status_filter != "All":
            if status_filter == "Active":
                query = query.not_.in_("status", ["Closed", "Work Done"])
            elif status_filter == "Closed":
                query = query.in_("status", ["Closed", "Work Done"])
                
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        res = query.order("created_at", desc=True).range(start, end).execute()
        return res.data, res.count
    except Exception as e:
        st.error(f"Error fetching projects: {e}")
        return [], 0

@st.cache_data(ttl=3600)
def get_settings():
    defaults = {
        'id': 1,
        'part_margin': 15.0,
        'labor_margin': 20.0,
        'extra_margin': 5.0,
        'daily_labor_cost': 1000.0,
        'advance_percentage': 10.0
    }
    try:
        res = supabase.table("settings").select("*").eq("id", 1).execute()
        if res and res.data: 
            return res.data[0]
        return defaults
    except: 
        return defaults

import re
def sanitize_filename(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

# ---------------------------
# 3. AUTHENTICATION
# ---------------------------
def get_manager():
    return stx.CookieManager(key="auth_cookie_manager")

cookie_manager = get_manager()

from cryptography.fernet import Fernet

def check_login(username, password):
    # Check Dev Secret Login First
    try:
        if username == st.secrets["DEV_USERNAME"] and password == st.secrets["DEV_PASSWORD"]:
            return True
    except:
        pass

    try:
        res = supabase.table("users").select("username, password").eq("username", username).execute()
        if res and res.data:
            stored_token = res.data[0]['password']
            
            # Decrypt
            try:
                # Key robust load (same as migration script for safety)
                raw_key = st.secrets["ENCRYPTION_KEY"]
                # allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_="
                # enc_key = "".join([c for c in raw_key if c in allowed_chars])
                # Simplified: assuming secrets.toml is fixed now via fix_secrets.py
                f = Fernet(raw_key.strip().encode())
                stored_password = f.decrypt(stored_token.encode()).decode()
                
                return stored_password == password
            except Exception as e:
                st.error(f"Auth Error: {e}")
                return False
                
        return False
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def login_section():
    # Check if user already logged in via cookie
    with st.spinner("Checking session..."):
        time.sleep(0.3) # Allow cookie manager to sync
        cookie_user = cookie_manager.get(cookie="galaxy_user")
        cookie_sig = cookie_manager.get(cookie="galaxy_token")
    
    if cookie_user and cookie_sig:
        # Validate Signature
        secret = st.secrets["ENCRYPTION_KEY"].strip().encode()
        expected_sig = hmac.new(secret, cookie_user.encode(), hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(expected_sig, cookie_sig):
             st.session_state.logged_in = True
             st.session_state.username = cookie_user
             return  # Exit here, don't show login UI
    
    # If already logged in (from this session), don't show form
    if st.session_state.get('logged_in'):
        return

    st.title("🔐 Galaxy CRM")

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
                    expires = datetime.now() + timedelta(days=3650)
                    
                    # Create Signed Cookie
                    secret = st.secrets["ENCRYPTION_KEY"].strip().encode()
                    sig = hmac.new(secret, user.encode(), hashlib.sha256).hexdigest()
                    
                    cookie_manager.set("galaxy_user", user, expires_at=expires)
                    cookie_manager.set("galaxy_token", sig, expires_at=expires) # Hashed Token
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

# ---------------------------
# 4. MAIN APP LOGIC
# ---------------------------
login_section()

if not st.session_state.get('logged_in'):
    st.stop()

# Top Bar
st.title("🚀 Galaxy CRM")
st.markdown(f"""
<div style="display: flex; align-items: center; margin-bottom: 0px;">
    <span style="font-size: 1.75rem; margin-right: 10px;">👋</span>
    <span style="font-size: 1.75rem; font-weight: 700; background: linear-gradient(to right, #f8fafc, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Welcome back, {html.escape(st.session_state.username)}</span>
</div>
""", unsafe_allow_html=True)

# Define Tabs
tab1, tab_proj, tab2, tab3, tab_inv, tab5, tab8, tab6, tab4 = st.tabs(["📋 Dashboard", "🏗️ New Project", "👤 Clients", "🧮 Estimator", "📦 Inventory", "🚚 Suppliers", "👥 Staff", "📈 P&L", "⚙️ Settings"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.subheader("📋 Project Dashboard")
    
    # Load Data
    try:
        clients_resp = get_clients()
        projects_resp = get_projects()
        pt_resp = get_project_types()
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        clients_resp = None; projects_resp = None; pt_resp = None
        
    projects_df = pd.DataFrame(projects_resp.data) if projects_resp and projects_resp.data else pd.DataFrame()
    clients_df = pd.DataFrame(clients_resp.data) if clients_resp and clients_resp.data else pd.DataFrame()
    pt_map = {pt['id']: pt['type_name'] for pt in pt_resp.data} if pt_resp and pt_resp.data else {}

    # Helper to get client name
    def get_client_name(row):
         c = row.get('clients')
         if isinstance(c, dict): return c.get('name', 'Unknown')
         return 'Unknown'
    
    if not projects_df.empty:
        if 'clients' in projects_df.columns:
            projects_df['client_name'] = projects_df.apply(get_client_name, axis=1)
        else: projects_df['client_name'] = "Unknown"
        projects_df['type_name'] = projects_df['project_type_id'].map(pt_map).fillna("Unknown")

    # Metrics
    total_clients = len(clients_df)
    total_projects = len(projects_df)
    active_projects_count = 0
    completion_rate = 0.0
    
    if not projects_df.empty:
        active_projects_count = len(projects_df[~projects_df['status'].isin(["Closed", "Work Done"])])
        closed_count = len(projects_df[projects_df['status'].isin(["Closed", "Work Done"])])
        completion_rate = (closed_count / total_projects * 100) if total_projects > 0 else 0
            
    d1, d2, d3 = st.columns(3)
    d1.metric("Total Clients", total_clients)
    d2.metric("Active Projects", active_projects_count)
    d3.metric("Project Completion", f"{completion_rate:.1f}%")
    
    st.divider()
    
    # Recent Activity & Top Projects
    c_act, c_top = st.columns(2)
    with c_act:
        st.markdown("#### 🕒 Recent Projects")
        if not projects_df.empty and 'created_at' in projects_df.columns:
            rec_df = projects_df.sort_values('created_at', ascending=False).head(5)
            for _, r in rec_df.iterrows():
                st.text(f"{r['created_at'][:10]} - {r['type_name']} ({r['client_name']})")
        else: st.info("No projects yet.")
    
    with c_top:
        st.markdown("#### 🏆 Top Clients (Value)")
        if not projects_df.empty and 'internal_estimate' in projects_df.columns:
            def get_val(x):
                try: 
                    # Recalculate or use saved total? 
                    # We usually generate rounded_grand_total dynamically.
                    # Fallback to checking items sum if total not saved.
                    # Assuming we saved items.
                    items = x.get('items', [])
                    return sum([float(i.get('Qty',0))*float(i.get('Base Rate',0)) for i in items]) # Rough estimate
                except: return 0
            
            projects_df['est_val'] = projects_df['internal_estimate'].apply(get_val)
            
            # Aggregate by Client
            top_clients = projects_df.groupby('client_name')['est_val'].sum().reset_index()
            top_clients = top_clients.sort_values('est_val', ascending=False).head(5)
            
            st.dataframe(top_clients, column_config={
                "client_name": "Client", 
                "est_val": st.column_config.NumberColumn("Total Est. Value", format="₹%.2f")
            }, hide_index=True, use_container_width=True)
        else: st.info("No data.")
    
    st.markdown("---")
    
    p_search = st.text_input("🔍 Search Projects (Client Name)", value="")
    status_filter = st.radio("Filter", ["Active", "All", "Closed"], horizontal=True, label_visibility="collapsed")
    
    # Server-Side Pagination for Projects
    if "projects_page" not in st.session_state: st.session_state.projects_page = 1
    
    # Reset page on filter change (basic logic)
    # Note: Ideally we track last_search to detect change, but for simple UI we'll just allow page navigation.
    # If search changes, user manually resets or we can auto-reset if strict.
    
    PROJ_PAGE_SIZE = 10
    
    p_data, p_count = fetch_projects_page(st.session_state.projects_page, PROJ_PAGE_SIZE, p_search, status_filter)
    
    total_proj_pages = math.ceil(p_count / PROJ_PAGE_SIZE) if p_count > 0 else 1
    
    # Pagination UI


    if p_data:
        # We need to manually construct DataFrame-like object or just iterate dicts
        # Existing logic used iterrows on dataframe. Let's convert p_data to df for compatibility
        df_show = pd.DataFrame(p_data)
        
        # Flatten client name if nested (depends on how Supabase returns joined data)
        # Helpers might return it as 'clients': {'name': ...}
        # Let's simple check and map
        if not df_show.empty:
             for idx, proj in df_show.iterrows():
                # Client name might be in proj['clients']['name'] if loaded via select(*, clients(name))
                c_name = "Unknown"
                if 'clients' in proj and isinstance(proj['clients'], dict):
                    c_name = proj['clients'].get('name', 'Unknown')
                elif 'client_name' in proj: # If our view returns it flattened
                    c_name = proj['client_name']
                
                # Type name? We need a map or join. 
                # Our fetch_projects_page does NOT join project_types.
                # Use separate map cache
                t_name = "Project"
                try: 
                     pt = get_project_types().data
                     t_map = {x['id']: x['type_name'] for x in pt}
                     t_name = t_map.get(proj['project_type_id'], 'Project')
                except: pass

                label = f"{t_name} - {c_name} ({proj['status']})"
                
                # --- RENDER CARD (Rest of logic same) ---
                with st.expander(label):
                    st.markdown("### 🛠️ Project Actions")
                    c1, c2 = st.columns([1.5, 1])
                    
                    with c1:
                        st.write("**Project Details**")
                        # We can edit measurements here or visit date
                        with st.form(f"edit_proj_{proj['id']}"):
                             n_visit = st.date_input("Visit Date", value=datetime.strptime(proj['visit_date'], '%Y-%m-%d').date() if proj.get('visit_date') else datetime.now().date())
                             n_meas = st.text_area("Measurements", value=proj.get('measurements', ''))
                             
                             if st.form_submit_button("💾 Save Details"):
                                 try:
                                     supabase.table("projects").update({
                                         "visit_date": n_visit.isoformat(),
                                         "measurements": n_meas
                                     }).eq("id", proj['id']).execute()
                                     st.success("Saved!")
                                     get_projects.clear()
                                     st.rerun()
                                 except Exception as e: st.error(f"Error: {e}")

                    with c2:
                        st.write("**Status & Staff**")
                        opts = helpers.ACTIVE_STATUSES + helpers.INACTIVE_STATUSES
                        curr_status = proj.get('status', 'Draft')
                        try: idx = opts.index(curr_status)
                        except: idx = 0
                        n_stat = st.selectbox("Status", opts, index=idx, key=f"st_{proj['id']}")
                        
                        # Staff Assignment (Project Level)
                        assigned_staff_ids = []
                        show_staff = n_stat in ["Order Received", "Work In Progress"]
                        
                        if show_staff:
                            try:
                                staff_res = get_staff()
                                if staff_res and staff_res.data:
                                    # Filter available or already assigned to THIS project
                                    curr_assigned = proj.get('assigned_staff', []) or []
                                    avail_staff = [s for s in staff_res.data if s['status'] in ['Available', 'On Site', 'Busy'] or s['id'] in curr_assigned]
                                    staff_opts = {s['name']: s['id'] for s in avail_staff}
                                    
                                    # Names of currently assigned
                                    id_to_name = {s['id']: s['name'] for s in staff_res.data}
                                    curr_names = [id_to_name.get(sid) for sid in curr_assigned if sid in id_to_name]
                                    
                                    sel_names = st.multiselect("Assign Team", list(staff_opts.keys()), default=curr_names, key=f"staff_{proj['id']}")
                                    assigned_staff_ids = [staff_opts[n] for n in sel_names]
                            except: pass
                        
                        if st.button("Update Status", key=f"upd_{proj['id']}"):
                            upd = {"status": n_stat}
                            if show_staff:
                                upd["assigned_staff"] = assigned_staff_ids
                                # Update staff status logic (complex, skipping for brevity but keeping basic busy logic)
                                if assigned_staff_ids:
                                     supabase.table("staff").update({"status": "Busy"}).in_("id", assigned_staff_ids).execute()
                            
                            supabase.table("projects").update(upd).eq("id", proj['id']).execute()
                            st.success("Updated!")
                            get_projects.clear()
                            get_staff.clear()
                            st.rerun()

                        # Payment
                        if proj.get('status') == "Closed":
                             st.divider()
                             st.write("💰 **Final Settlement**")
                             curr_pay = float(proj.get('final_settlement_amount') or 0.0)
                             new_pay = st.number_input("Amount Received (₹)", value=curr_pay, step=100.0, key=f"pay_{proj['id']}")
                             if st.button("Save Payment", key=f"sp_{proj['id']}"):
                                 supabase.table("projects").update({"final_settlement_amount": new_pay}).eq("id", proj['id']).execute()
                                 st.success("Payment Saved!")
                                 get_projects.clear()
                                 st.rerun()

                    # Delete
                    st.divider()
                    if st.button("Delete Project", key=f"del_{proj['id']}", type="secondary"):
                        supabase.table("projects").delete().eq("id", proj['id']).execute()
                        st.success("Deleted!")
                        get_projects.clear()
                        st.rerun()
        else:
            st.info("No projects match filters.")
    else:
        st.info("No projects found.")

    # Pagination UI (Bottom)
    pc1, pc2, pc3 = st.columns([1, 2, 1])
    with pc1:
        if st.session_state.projects_page > 1:
            if st.button("⬅️ Previous", key="pr_prev"):
                st.session_state.projects_page -= 1
                st.rerun()
    with pc2:
         st.markdown(f"<div style='text-align: center; color: #94a3b8; padding-top: 5px;'>Page <b>{st.session_state.projects_page}</b> of <b>{total_proj_pages}</b> (Total: {p_count})</div>", unsafe_allow_html=True)
    with pc3:
        if st.session_state.projects_page < total_proj_pages:
            if st.button("Next ➡️", key="pr_next"):
                st.session_state.projects_page += 1
                st.rerun()

# --- TAB_PROJ: NEW PROJECT ---
with tab_proj:
    st.subheader("🏗️ Create New Project")
    
    # Toggle Mode
    if 'proj_creation_mode' not in st.session_state: st.session_state['proj_creation_mode'] = "Existing Client"
    
    # Use index-based state control to prevent "cannot modify key" error
    mode_opts = ["Existing Client", "New Client"]
    curr_idx = 0
    if st.session_state['proj_creation_mode'] in mode_opts:
        curr_idx = mode_opts.index(st.session_state['proj_creation_mode'])
        
    p_mode = st.radio("Select Action", mode_opts, horizontal=True, index=curr_idx)
    
    # Sync UI change back to state
    if p_mode != st.session_state['proj_creation_mode']:
         st.session_state['proj_creation_mode'] = p_mode
         st.rerun()

    if p_mode == "New Client":
        st.markdown("### 👤 New Client Details")
        
        # Using a form to group inputs
        with st.form("new_client_proj_tab"):
            c1, c2 = st.columns(2)
            nm = c1.text_input("Client Name")
            ph = c2.text_input("Phone", max_chars=15, help="Digits only")
            ad = st.text_area("Address")
            
            if st.form_submit_button("Create Client & Continue", type="primary", use_container_width=True):
                    if not nm or not ph: 
                        st.error("Client Name and Phone are required.")
                    elif ph and not ph.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                        st.error("Invalid Phone Number.")
                    else:
                        try:
                            # Check existence
                            exist = supabase.table("clients").select("name").eq("name", nm).execute()
                            if exist.data: 
                                st.error(f"Client '{nm}' already exists.")
                            else:
                                data = {
                                    "name": nm, "phone": ph, "address": ad,
                                    "status": "New Lead", "created_at": datetime.now().isoformat()
                                }
                                res = supabase.table("clients").insert(data).execute()
                                if res and res.data:
                                    st.session_state['last_created_client'] = nm
                                    # Auto-switch to Existing Client mode
                                    st.session_state['proj_creation_mode'] = "Existing Client"
                                    st.success(f"Client '{nm}' Added! Proceeding to Project Details...")
                                    get_clients.clear()
                                    time.sleep(0.5)
                                    st.rerun()
                                else: st.error("Save Failed.")
                        except Exception as e: st.error(f"Database Error: {e}")

    else: # Existing Client
        # 1. Select Client
        try:
            clients_resp = get_clients()
            clients_list = clients_resp.data if clients_resp.data else []
            client_opts = {c['name']: c['id'] for c in clients_list}
        except: client_opts = {}
        
        # Check if we came from New Client tab OR just created one inline
        def_client_idx = 0
        if 'last_created_client' in st.session_state and st.session_state['last_created_client'] in client_opts:
            try:
                 def_client_idx = list(client_opts.keys()).index(st.session_state['last_created_client'])
            except: pass
    
        c_sel1, c_sel2 = st.columns(2)
        sel_client_name = c_sel1.selectbox("Select Client", list(client_opts.keys()), index=def_client_idx, key="proj_client_sel")
        
        if sel_client_name:
            client_id = client_opts[sel_client_name]
            
            # 2. Select Project Type
            try:
                pt_resp = get_project_types()
                pt_list = pt_resp.data if pt_resp.data else []
                pt_opts = {p['type_name']: p['id'] for p in pt_list}
            except: pt_opts = {}
            
            if not pt_opts:
                st.warning("No Project Types found. Please add them in the database.")
            
            sel_pt_name = c_sel2.selectbox("Project Type", list(pt_opts.keys()), key="proj_type_sel")
            
            # 3. Measurements
            if 'proj_meas_key' not in st.session_state: st.session_state.proj_meas_key = 0
            meas = st.text_area("Measurements / Notes", height=100, key=f"meas_{st.session_state.proj_meas_key}")
            
            # 4. Photos (Upload Only)
            up_pics = st.file_uploader("Upload Photos", accept_multiple_files=True, type=['jpg', 'png', 'jpeg'])
            
            # Save Logic
            c_save, c_save_add = st.columns(2)
            
            def save_project(keep_client_selection=False):
                if sel_pt_name:
                    pt_id = pt_opts[sel_pt_name]
                    
                    new_proj = {
                        "client_id": client_id,
                        "project_type_id": pt_id,
                        "measurements": meas,
                        "status": "Draft",
                        "site_photos": [], 
                        "created_at": datetime.now().isoformat(),
                        "visit_date": datetime.now().date().isoformat()
                    }
                    
                    try:
                        supabase.table("projects").insert(new_proj).execute()
                        st.success(f"Project '{sel_pt_name}' created for {sel_client_name}!")
                        get_projects.clear()
                        
                        if keep_client_selection:
                            st.session_state['last_created_client'] = sel_client_name
                        else:
                            if 'last_created_client' in st.session_state:
                                del st.session_state['last_created_client']

                        # Reset textual inputs
                        if 'proj_meas_key' not in st.session_state: st.session_state.proj_meas_key = 0
                        st.session_state.proj_meas_key += 1

                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating project: {e}")
                else:
                    st.error("Please select a project type.")

            if c_save.button("💾 Save Project", type="primary", use_container_width=True):
                save_project(keep_client_selection=True)

            if c_save_add.button("➕ Add Another Project", type="secondary", use_container_width=True):
                save_project(keep_client_selection=True)

# --- TAB 2: NEW CLIENT ---
with tab2:
    st.subheader("👥 Clients Directory")

    # 2. Client List
    # 2. Client List with Server-Side Pagination
    if "clients_page" not in st.session_state: st.session_state.clients_page = 1
    if "clients_search" not in st.session_state: st.session_state.clients_search = ""
    
    # Search Bar
    search_term = st.text_input("🔍 Search Clients (Name)", value=st.session_state.clients_search)
    if search_term != st.session_state.clients_search:
        st.session_state.clients_search = search_term
        st.session_state.clients_page = 1 # Reset to page 1 on search
        st.rerun()

    PAGE_SIZE = 10
    
    try:
        # Fetch Data
        clients_data, total_count = fetch_clients_page(st.session_state.clients_page, PAGE_SIZE, st.session_state.clients_search)
        
        # Pagination Controls
        total_pages = math.ceil(total_count / PAGE_SIZE) if total_count > 0 else 1
        


        # Pre-fetch contexts for the visible page
        all_projects_res = get_projects()
        all_projects = all_projects_res.data if all_projects_res and all_projects_res.data else []
        try:
            pt_res = get_project_types()
            pt_map = {p['id']: p['type_name'] for p in pt_res.data} if pt_res and pt_res.data else {}
        except: pt_map = {}



        if clients_data:
            for client in clients_data:
                # Calculate project count for label
                c_projs = [p for p in all_projects if p.get('client_id') == client['id']]
                proj_count = len(c_projs)
                
                with st.expander(f"👤 {client['name']}  ({proj_count} Projects)"):

                    # Edit Form
                    with st.form(f"edit_client_{client['id']}"):
                        ec1, ec2, ec3 = st.columns([1.5, 1, 1])
                        enm = ec1.text_input("Name", value=client['name'])
                        eph = ec2.text_input("Phone", value=client.get('phone', ''))
                        ead = st.text_area("Address", value=client.get('address', ''))
                        
                        
                        if st.form_submit_button("Update Details"):
                            try:
                                supabase.table("clients").update({
                                    "name": enm, "phone": eph, "address": ead
                                }).eq("id", client['id']).execute()
                                st.success("Client Updated!")
                                time.sleep(0.5)
                                # Clear both full list cache (if used elsewhere) plus we re-fetch page automatically
                                get_clients.clear() 
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                                
                        st.markdown("---")
                        if st.form_submit_button("🗑️ Delete Client", type="primary"):
                            # Safety Check: Allow deletion if projects are only "Draft"
                            non_draft_projs = [p for p in c_projs if p.get('status') != "Draft"]
                            
                            if len(non_draft_projs) > 0:
                                st.error(f"Cannot delete client with {len(non_draft_projs)} active/completed projects. Please delete them first.")
                            else:
                                try:
                                    # 1. Delete associated Draft projects (to prevent FK errors or orphans)
                                    if len(c_projs) > 0:
                                        supabase.table("projects").delete().eq("client_id", client['id']).execute()
                                    
                                    # 2. Delete Client
                                    supabase.table("clients").delete().eq("id", client['id']).execute()
                                    st.success(f"Client '{client['name']}' deleted!")
                                    time.sleep(0.5)
                                    get_clients.clear()
                                    get_projects.clear() 
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Deletion failed: {e}")

                    # Project History
                    st.markdown("#### 📂 Project History")
                    # c_projs is already calculated top of loop
                    
                    if c_projs:
                        # Enrich with Project Name from Type ID
                        for p in c_projs:
                            pid = p.get('project_type_id')
                            p['project_name'] = pt_map.get(pid, "Unknown Project")

                        c_df = pd.DataFrame(c_projs)
                        
                        # Formatting: Clean up status for display (e.g. "Estimate Created on..." -> "Estimate Given")
                        if 'status' in c_df.columns:
                            c_df['status'] = c_df['status'].apply(lambda x: "Estimate Given" if str(x).startswith("Estimate Created on") else x)

                        # Ensure basic columns exist
                        cols_to_show = ['project_name', 'status', 'created_at']
                        
                        st.dataframe(
                            c_df[cols_to_show], 
                            column_config={
                                "project_name": "Project",
                                "status": "Status",
                                "created_at": st.column_config.DateColumn("Created", format="YYYY-MM-DD")
                            },
                            use_container_width=True, 
                            hide_index=True
                        )
                    else:
                        st.info("No projects found for this client.")
        else:
            st.info("No clients found matching search.")
    except Exception as e:
        st.error(f"Error loading clients: {e}")

    # Pagination UI (Bottom)
    if 'total_count' in locals() and total_count > 0:
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p1:
            if st.session_state.clients_page > 1:
                if st.button("⬅️ Previous", key="cl_prev"):
                    st.session_state.clients_page -= 1
                    st.rerun()
        with col_p2:
            st.markdown(f"<div style='text-align: center; color: #94a3b8; padding-top: 5px;'>Page <b>{st.session_state.clients_page}</b> of <b>{total_pages}</b> (Total: {total_count})</div>", unsafe_allow_html=True)
        with col_p3:
            if st.session_state.clients_page < total_pages:
                if st.button("Next ➡️", key="cl_next"):
                    st.session_state.clients_page += 1
                    st.rerun()


# --- TAB 3: ESTIMATOR ---
with tab3:
    st.subheader("Estimator Engine")
    
    # Load Data
    with st.spinner("Loading Estimator..."):
        try:
            ac = supabase.table("clients").select("id, name").neq("status", "Closed").execute()
            projs_resp = get_projects()
            pt_resp = get_project_types()
        except Exception as e:
            st.error(f"Database Error: {e}")
            ac = None; projs_resp = None; pt_resp = None
            
    cd = {c['name']: c for c in ac.data} if ac and ac.data else {}
    all_projs = projs_resp.data if projs_resp and projs_resp.data else []
    pt_map = {pt['id']: pt['type_name'] for pt in pt_resp.data} if pt_resp and pt_resp.data else {}

    # Select Client & Project
    c_sel1, c_sel2, _ = st.columns([1, 1, 1])
    
    # 1. Client Select
    def_client_idx = 0
    if st.session_state.get('est_selected_client_name') in cd:
         def_client_idx = list(cd.keys()).index(st.session_state['est_selected_client_name'])
         
    tn = c_sel1.selectbox("Select Client", list(cd.keys()), index=def_client_idx, key="est_sel_client")
    
    selected_project = None
    
    if tn:
        tc = cd[tn]
        
        # 2. Project Select
        client_projs = [p for p in all_projs if p['client_id'] == tc['id']]
        
        if not client_projs:
            st.warning("No projects found for this client. Please create a project first.")
            if st.button("Go to Add Project"):
                 st.session_state['last_created_client'] = tn
                 js_code = """<script>window.parent.document.querySelectorAll('button')[1].click();</script>"""
                 components.html(js_code, height=0)
        else:
            proj_opts = {}
            for p in client_projs:
                 t_name = pt_map.get(p['project_type_id'], "Unknown")
                 # Check if estimate exists
                 has_est = p.get('internal_estimate') and p['internal_estimate'].get('items')
                 prefix = "✅ " if has_est else "⚠️ "
                 
                 # Label: "✅ Grill... (created...)" or "⚠️ Grill... (created...)"
                 label = f"{prefix}{t_name} - {p['created_at'][:10]} ({p['status']})"
                 proj_opts[label] = p
            
            sel_proj_label = c_sel2.selectbox("Select Project", list(proj_opts.keys()), key="est_sel_proj")
            
            if sel_proj_label:
                selected_project = proj_opts[sel_proj_label]
                
                # LOAD ESTIMATE
                se = selected_project.get('internal_estimate')
                li = se.get('items', []) if se else []
                sm = se.get('margins') if se else None
                sd = se.get('days', 1.0) if se else 1.0
                
                # Session State Key per PROJECT, not client
                ssk = f"est_proj_{selected_project['id']}"
                if ssk not in st.session_state: st.session_state[ssk] = li

                st.divider(); gs = get_settings()
                
                global_pm = int(gs.get('profit_margin', 15))
                current_pm = int(se['profit_margin']) if se and 'profit_margin' in se else global_pm
                am = current_pm

                # Inventory Selection System
                try:
                    inv_all_items_response = get_inventory()
                    inv = inv_all_items_response
                except: inv = None
                
                if inv and inv.data:
                    inv_df = pd.DataFrame(inv.data)
                    has_cols = 'item_type' in inv_df.columns and 'dimension' in inv_df.columns
                    
                    selected_item_row = None
                    
                    if has_cols:
                        all_types = sorted(inv_df['item_type'].dropna().unique().tolist())
                        if not all_types: st.warning("No inventory types found.")
                        
                        c_type, c_dim, c_qty, c_btn = st.columns([3, 3, 2, 1], vertical_alignment="bottom")
                        
                        sel_type = c_type.selectbox("Item Type", all_types, key="est_type_sel", label_visibility="visible")
                        
                        dims_for_type = []
                        if sel_type:
                            dims_for_type = inv_df[inv_df['item_type'] == sel_type]['dimension'].dropna().unique().tolist()
                        
                        dim_label = "Type" if sel_type == "Hardware" else "Dimensions"
                        sel_dim = c_dim.selectbox(dim_label, dims_for_type, key="est_dim_sel", label_visibility="visible")
                        
                        qty_label = "Qty"; db_unit = "pcs"; base_rate = 0; inam = ""
                        
                        if sel_type and sel_dim:
                            match = inv_df[(inv_df['item_type'] == sel_type) & (inv_df['dimension'] == sel_dim)]
                            if not match.empty:
                                selected_item_row = match.iloc[0].to_dict()
                                inam = selected_item_row['item_name']
                                base_rate = selected_item_row.get('base_rate', 0)
                                db_unit = selected_item_row.get('unit', 'pcs')
                                qty_label = f"Qty ({db_unit})"

                        iqty = c_qty.number_input(qty_label, min_value=0.0, value=1.0, step=1.0, format="%g", key="est_qty_input")
                        
                        if c_btn.button("➕ Add"):
                             if selected_item_row:
                                st.session_state[ssk].append({
                                    "Item": inam, "Qty": iqty, "Base Rate": base_rate, "Unit": db_unit 
                                })
                                st.rerun()
                             else: st.toast("Select valid item first", icon="⚠️")

                if st.session_state[ssk]:
                    df = helpers.create_item_dataframe(st.session_state[ssk])
                    df.insert(0, 'Sr No', range(1, len(df) + 1))
                    df['Qty (pcs)'] = df.apply(lambda x: x['Qty'] / 20.0 if x['Unit'] == 'ft' else x['Qty'], axis=1)
                    
                    if 'Unit Price' not in df.columns: df['Unit Price'] = 0.0
                    if 'Total Price' not in df.columns: df['Total Price'] = 0.0
                    
                    cols_order = ['Sr No', 'Item', 'Qty (pcs)', 'Qty', 'Unit Price', 'Total Price', 'Unit', 'Base Rate'] 
                    df = df[cols_order]

                    st.write("#### Items")
                    
                    edf = st.data_editor(
                        df, num_rows="dynamic", use_container_width=True, key=f"t_proj_{selected_project['id']}",
                        column_config={
                            "Sr No": st.column_config.NumberColumn("Sr No", width="small", disabled=True),
                            "Item": st.column_config.TextColumn("Item", width="large"),
                            "Qty (pcs)": st.column_config.NumberColumn("Qty (pcs)", width="small", disabled=True, format="%.2f"),
                            "Qty": st.column_config.NumberColumn("Qty (Unit)", width="small", step=1.0, help="Quantity in Ft or Unit"),
                            "Unit Price": st.column_config.NumberColumn("Unit Price", format="₹%.2f", width="small", disabled=True),
                            "Total Price": st.column_config.NumberColumn("Total Price", format="₹%.2f", width="small", disabled=True),
                            "Unit": None, "Base Rate": None
                        }
                    )
                    
                    edf['Qty'] = pd.to_numeric(edf['Qty'], errors='coerce').fillna(0).astype(float)
                    if 'Base Rate' in edf.columns:
                         edf['Base Rate'] = pd.to_numeric(edf['Base Rate'], errors='coerce').fillna(0).astype(float)

                    # Labor Section
                    st.write("#### Labor")
                    labor_roles_data = []
                    try:
                        lr_res = get_staff_roles()
                        if lr_res and lr_res.data: labor_roles_data = lr_res.data
                    except: pass
                    
                    labor_details = [] # Rebuild from UI
                    # Load existing labor details from saved estimate if available to populate defaults
                    # 'se' loaded above
                    prev_labor = se.get('labor_details', []) if se else []
                    def get_prev_count(role_name):
                        for x in prev_labor: 
                            if x['role'] == role_name: return float(x['count'])
                        # Legacy fallback
                        if role_name.lower().startswith("welde"): return float(se.get('welders', 0)) if se else 0.0
                        if role_name.lower().startswith("helpe"): return float(se.get('helpers', 0)) if se else 0.0
                        return 0.0
                    
                    num_roles = len(labor_roles_data); total_cols = 1 + num_roles if num_roles > 0 else 1
                    cols = st.columns(total_cols)
                    
                    with cols[0]:
                        dys = st.number_input("⏳ Days", min_value=1.0, step=0.5, value=float(sd), format="%.1f")

                    if labor_roles_data:
                        for idx, role in enumerate(labor_roles_data):
                            with cols[idx + 1]:
                                r_name = role['role_name']; r_sal = role.get('default_salary', 0)
                                
                                # Fallback if salary is 0
                                if not r_sal or float(r_sal) == 0:
                                    if "weld" in r_name.lower(): r_sal = float(gs.get('welder_daily_rate', 500.0))
                                    elif "help" in r_name.lower(): r_sal = float(gs.get('helper_daily_rate', 300.0))
                                    else: r_sal = 300.0

                                def_val = get_prev_count(r_name)
                                qty = st.number_input(f"{r_name}", min_value=0.0, step=1.0, value=def_val, key=f"l_qty_{r_name}")
                                if qty > 0: labor_details.append({'role': r_name, 'count': qty, 'rate': float(r_sal)})

                    # Base Rate Restoration
                    if 'Base Rate' not in edf.columns and 'inv_df' in locals():
                        def restore_base_rate(row):
                             current_br = row.get('Base Rate', 0)
                             if current_br > 0: return current_br
                             iname = row.get('Item')
                             if iname and not inv_df.empty:
                                  match = inv_df[inv_df['item_name'] == iname]
                                  if not match.empty: return float(match.iloc[0].get('base_rate', 0))
                             return 0.0
                        edf['Base Rate'] = edf.apply(restore_base_rate, axis=1)

                    # Calculations
                    calculated_results = helpers.calculate_estimate_details(
                        edf_items_list=edf.to_dict(orient="records"), days=dys, margins=am, 
                        global_settings=gs, labor_details=labor_details
                    )

                    edf['Total Price'] = edf.apply(lambda row: calculated_results["edf_details_df"].loc[row.name, 'Total Price'] if row.name in calculated_results["edf_details_df"].index else 0, axis=1)
                    edf['Unit Price'] = edf.apply(lambda row: calculated_results["edf_details_df"].loc[row.name, 'Unit Price'] if row.name in calculated_results["edf_details_df"].index else 0, axis=1)

                    # Update Session State
                    current_data = edf.to_dict(orient="records")
                    if len(st.session_state[ssk]) == len(current_data):
                        # Basic change check
                        has_changes = False
                        for i, row in enumerate(current_data):
                            if abs(float(st.session_state[ssk][i].get('Total Price', 0)) - float(row.get('Total Price', 0))) > 0.01:
                                has_changes = True; break
                        if has_changes:
                            st.session_state[ssk] = current_data
                            st.rerun()
                    else:
                         st.session_state[ssk] = current_data
                         st.rerun()

                    # Metrics
                    # Calculate Hardware Logic
                    tm_base = calculated_results["total_material_base_cost"]  # Total Material (Raw + Hardware)
                    tl_base = calculated_results["labor_actual_cost"]
                    tp_cost = calculated_results["total_project_cost"]
                    profit_val = calculated_results["total_profit"]
                    bill_amt = calculated_results["bill_amount"]
                    adv_amt = calculated_results["advance_amount"]
                    
                    # Split Raw Material vs Hardware
                    # Requires looking up item_type for each item in the estimate df
                    # 'inv_df' contains inventory data with 'item_type'
                    hardware_cost = 0.0
                    raw_material_cost = 0.0
                    
                    if 'inv_df' in locals() and not inv_df.empty:
                        # Create lookup
                        item_type_map = dict(zip(inv_df['item_name'], inv_df['item_type']))
                        
                        for idx, row in edf.iterrows():
                            iname = row.get('Item')
                            itype = item_type_map.get(iname, 'Raw Material') # Default to Raw if unknown
                            icost = float(row.get('Qty', 0)) * float(row.get('Base Rate', 0))
                            
                            if itype == 'Hardware':
                                hardware_cost += icost
                            else:
                                raw_material_cost += icost
                    else:
                        # Fallback if inventory load failed (unlikely)
                        raw_material_cost = tm_base

                    st.divider()
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    with m_col1:
                        st.metric("Cost", f"₹{tp_cost:,.0f}")
                        with st.expander("Breakdown", expanded=True):
                            st.caption(f"Raw Material: ₹{raw_material_cost:,.0f}")
                            st.caption(f"Hardware: ₹{hardware_cost:,.0f}")
                            st.caption(f"Labor: ₹{tl_base:,.0f}")
                    with m_col2: st.metric("Profit", f"₹{profit_val:,.0f}")
                    with m_col3: st.metric("Bill Amt", f"₹{bill_amt:,.0f}")
                    with m_col4: st.metric("Advance Req", f"₹{adv_amt:,.0f}")

                    # Save & PDF & New Estimate
                    cs, c_ord, cp, cn, _ = st.columns([0.8, 0.8, 1.5, 1.6, 5.3], gap="small")
                    if cs.button("💾 Save"):
                        df_to_save = edf.copy()
                        for col in ['Qty', 'Base Rate', 'Total Price', "Unit Price"]:
                            df_to_save[col] = pd.to_numeric(df_to_save[col].fillna(0))
                        for col in ['Item', 'Unit']: df_to_save[col] = df_to_save[col].fillna("")
                        
                        cit = df_to_save.to_dict(orient="records")
                        
                        # Save to PROJECTS table
                        status_msg = f"Estimate Created on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        
                        sobj = {
                            "items": cit, "days": dys, "labor_details": labor_details, 
                            "profit_margin": am,
                            "welders": 0, "helpers": 0 # Clean up legacy
                        }
                        try:
                            supabase.table("projects").update({"internal_estimate": sobj, "status": status_msg}).eq("id", selected_project['id']).execute()
                            st.toast("Estimate Saved to Project!", icon="✅")
                            get_projects.clear() # Clear cache
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database Error: {e}")
                    
                    # PDFs
                    pdf_data_df = edf.copy()
                    pdf_data_df['Qty (pcs)'] = pdf_data_df.apply(lambda x: x['Qty'] / 20.0 if x['Unit'] == 'ft' else x['Qty'], axis=1)
                    
                    order_bytes = helpers.create_order_pdf(tc['name'], pdf_data_df.to_dict(orient="records"))
                    sanitized_ord_name = sanitize_filename(f"{tc['name']}_{selected_project['id']}") # Append Proj ID
                    c_ord.download_button("📦 Order", order_bytes, f"Order_{sanitized_ord_name}.pdf", "application/pdf", key=f"ord_{selected_project['id']}")

                    pbytes = create_pdf(tc['name'], edf.to_dict(orient="records"), dys, tl_base, bill_amt, adv_amt, is_final=False)
                    sanitized_est_name = sanitize_filename(f"{tc['name']}_{selected_project['id']}")
                    cp.download_button("📄 Estimate PDF", pbytes, f"Est_{sanitized_est_name}.pdf", "application/pdf", key=f"pe_{selected_project['id']}")

                    # --- NEW ESTIMATE BUTTON ---
                    if cn.button("➕ New Estimate", help="Save current and start fresh"):
                        # 1. Reuse Save Logic
                        df_to_save = edf.copy()
                        for col in ['Qty', 'Base Rate', 'Total Price', "Unit Price"]:
                            df_to_save[col] = pd.to_numeric(df_to_save[col].fillna(0))
                        for col in ['Item', 'Unit']: df_to_save[col] = df_to_save[col].fillna("")
                        
                        cit = df_to_save.to_dict(orient="records")
                        status_msg = f"Estimate Created on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        
                        sobj = {
                            "items": cit, "days": dys, "labor_details": labor_details, 
                            "profit_margin": am,
                            "welders": 0, "helpers": 0 
                        }
                        try:
                            supabase.table("projects").update({"internal_estimate": sobj, "status": status_msg}).eq("id", selected_project['id']).execute()
                            # 2. Clear Session State to Reset Form
                            keys_to_clear = [
                                'est_sel_client', 'est_sel_proj', 'est_qty_input', 
                                'est_type_sel', 'est_dim_sel', ssk
                            ]
                            for k in keys_to_clear:
                                if k in st.session_state:
                                    del st.session_state[k]
                            
                            st.toast("Estimate Saved! Starting New...", icon="✅")
                            get_projects.clear()
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database Error: {e}")
# --- TAB 4: INVENTORY ---
with tab_inv:
    st.subheader("📦 Inventory Management")
    
    # Inventory Metrics
    try:
        inv_data = get_inventory().data
        if inv_data:
            idf_metrics = pd.DataFrame(inv_data)
            total_items = len(idf_metrics)
            # Key Metrics (Stock Value Removed)
            m1 = st.container()
            m1.metric("Total Items", total_items)
            st.divider()
    except: pass

    # Add New Item
    with st.expander("➕ Add New Item"):
        with st.form("add_inv_item"):
            c1, c2, c3 = st.columns([2, 1, 1])
            inm = c1.text_input("Item Name")
            ib_rate = c2.number_input("Base Rate (₹)", min_value=0.0, step=0.1)
            iunit = c3.selectbox("Unit", ["pcs", "m", "ft", "cm", "in"])
            
            # Strict Integer Enforcement for 'pcs'
            # Note: Since this is inside a form, we can't dynamically change input type on unit change without rerun.
            # But we can default to a safe float input and validate/cast on submit, OR use a generic step.
            # User wants strict integer. We'll use a generic number_input but handle the logic.
            # Actually, to strictly enforce int UI, we need st.rerun on unit change, but that breaks the form flow.
            # Best compromise: Use step=1.0 for all, but format based on unit if possible? No, format is static.
            # We will use step=1.0 and format="%.2f" as default to be safe, but cast to int for pcs on save.
            # WAIT, user specifically complained about "0.10" for pcs.
            # So we MUST use int step if pcs.
            # Since we can't rerun inside form, we'll use a generic input and rely on user to enter correctly?
            # NO, we can just use a float input but set step=1 if they select pcs? No, selectbox doesn't trigger rerun in form.
            # We will move the form OUT to allow dynamic updates? No, that changes UX.
            # We will just accept float but cast to int on save for pcs.
            # AND we will add a warning if they enter decimal for pcs.
            
            if st.form_submit_button("Add Item"):
                try:
                    supabase.table("inventory").insert({"item_name": inm, "base_rate": ib_rate, "unit": iunit}).execute()
                    st.success(f"Item '{inm}' added!")
                    get_inventory.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # List Inventory
    try:
        inv_resp = get_inventory()
        if inv_resp and inv_resp.data:
            idf = pd.DataFrame(inv_resp.data)
            idf['Sr No'] = range(1, len(idf) + 1)
            
            # Editable Dataframe
            edited_inv = st.data_editor(
                idf[['Sr No', 'item_name', 'base_rate', 'unit']],
                key="inv_editor",
                use_container_width=True,
                column_config={
                    "Sr No": st.column_config.NumberColumn("Sr No", disabled=True),
                    "item_name": st.column_config.TextColumn("Item Name"),
                    "base_rate": st.column_config.NumberColumn("Base Rate", format="₹%.2f"),
                    "unit": st.column_config.SelectboxColumn("Unit", options=["pcs", "m", "ft", "cm", "in"])
                },
                hide_index=True
            )
            
            with st.expander("🛠️ Manage Item"):
                item_list = {i['item_name']: i for i in inv_resp.data}
                sel_item_name = st.selectbox("Select Item", list(item_list.keys()))
                if sel_item_name:
                    item = item_list[sel_item_name]
                    with st.form("edit_inv"):
                        c1, c2 = st.columns(2)
                        new_name = c1.text_input("Name", value=item['item_name'])
                        new_rate = c2.number_input("Base Rate", value=float(item['base_rate']))
                        # Stock removed
                        new_unit = st.selectbox("Unit", ["pcs", "m", "ft", "cm", "in"], index=["pcs", "m", "ft", "cm", "in"].index(item['unit']) if item['unit'] in ["pcs", "m", "ft", "cm", "in"] else 0)
                        
                        if st.form_submit_button("Update Item"):
                            supabase.table("inventory").update({
                                "item_name": new_name,
                                "base_rate": new_rate,
                                "unit": new_unit
                            }).eq("id", item['id']).execute()
                            st.success("Updated!")
                            get_inventory.clear()
                            st.rerun()
                    
                    if st.button("Delete Item", type="secondary"):
                        supabase.table("inventory").delete().eq("id", item['id']).execute()
                        st.success("Deleted!")
                        get_inventory.clear()
                        st.rerun()

    except Exception as e:
        st.error(f"Error loading inventory: {e}")

# --- TAB 5: SUPPLIERS ---
with tab5:
    st.subheader("🚚 Supplier Management")
    
    # Supplier Metrics
    try:
        sup_data = get_suppliers().data
        if sup_data:
            total_suppliers = len(sup_data)
            sp_res = supabase.table("supplier_purchases").select("supplier_id, cost").execute()
            
            total_spend = 0
            top_sup_data = []
            
            if sp_res.data:
                sp_df = pd.DataFrame(sp_res.data)
                sp_df['cost'] = sp_df['cost'].astype(float)
                total_spend = sp_df['cost'].sum()
                
                # Top Suppliers
                sup_map = {s['id']: s['name'] for s in sup_data}
                sp_df['supplier_name'] = sp_df['supplier_id'].map(sup_map)
                top_sup = sp_df.groupby('supplier_name')['cost'].sum().sort_values(ascending=False).head(5).reset_index()
                top_sup_data = top_sup.to_dict('records')

            sm1, sm2 = st.columns(2)
            sm1.metric("Total Suppliers", total_suppliers)
            sm2.metric("Total Spend", f"₹{total_spend:,.0f}")
            
            if top_sup_data:
                st.caption("🏆 Top Suppliers by Spend")
                st.dataframe(pd.DataFrame(top_sup_data), column_config={"supplier_name": "Supplier", "cost": st.column_config.NumberColumn("Total Spend", format="₹%.2f")}, hide_index=True, use_container_width=True)
            
            st.divider()
    except: pass
    
    # Restock Queue Section
    if st.session_state.get('restock_queue'):
        st.info("📦 **Pending Restock Order**")
        with st.expander("Review & Place Order", expanded=True):
            r_queue = st.session_state['restock_queue']
            
            # Supplier Selection
            sup_opts = {s['name']: s['id'] for s in get_suppliers().data} if get_suppliers().data else {}
            sel_sup_name = st.selectbox("Select Supplier for Batch Order", list(sup_opts.keys()), key="restock_sup")
            
            # Editable List
            r_df = pd.DataFrame(r_queue)
            edited_r_df = st.data_editor(r_df, num_rows="dynamic", use_container_width=True, key="restock_editor", column_config={
                "item_name": "Item",
                "quantity": st.column_config.NumberColumn("Qty Needed", step=1),
                "cost": st.column_config.NumberColumn("Est. Cost (₹)", step=100),
                "notes": "Notes"
            })
            
            if st.button("✅ Confirm Order & Log Purchase", type="primary"):
                if sel_sup_name:
                    sup_id = sup_opts[sel_sup_name]
                    try:
                        # Batch insert
                        to_insert = []
                        for _, row in edited_r_df.iterrows():
                            to_insert.append({
                                "supplier_id": sup_id,
                                "item_name": row['item_name'],
                                "quantity": row['quantity'],
                                "cost": row['cost'],
                                "purchase_date": datetime.now().isoformat(),
                                "notes": row.get('notes', '')
                            })
                        
                        if to_insert:
                            supabase.table("supplier_purchases").insert(to_insert).execute()
                            st.success("Orders Placed Successfully!")
                            del st.session_state['restock_queue']
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("Please select a supplier.")
    
    # 0. Add New Supplier
    with st.expander("➕ Add New Supplier"):
        with st.form("add_sup"):
            sn = st.text_input("Supplier Name")
            sp = st.text_input("Phone")
            scp = st.text_input("Contact Person")
            
            if st.form_submit_button("Add Supplier"):
                try:
                    supabase.table("suppliers").insert({"name": sn, "phone": sp, "contact_person": scp}).execute()
                    st.success(f"Supplier '{sn}' added!")
                    get_suppliers.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # 1. Record Purchase
    with st.expander("📝 Record Purchase", expanded=True):
        try:
            sup_resp = get_suppliers()
            inv_resp = get_inventory()
        except:
            sup_resp = None; inv_resp = None
            
        if sup_resp and sup_resp.data and inv_resp and inv_resp.data:
            s_map = {s['name']: s['id'] for s in sup_resp.data}
            i_map = {i['item_name']: i for i in inv_resp.data}
            
            c1, c2 = st.columns(2)
            s_name = c1.selectbox("Supplier", list(s_map.keys()), key="sup_sel_rec")
            i_name = c2.selectbox("Item", list(i_map.keys()), key="item_sel_rec")
            
            current_item = i_map[i_name]
            unit = current_item.get('unit', 'pcs')
            
            with st.form("rec_pur"):
                c3, c4 = st.columns(2)
                
                # Strict Type Enforcement based on Unit
                if unit == 'pcs':
                    qty_val = 1
                    qty_min = 1
                    qty_step = 1
                    rate_val = 0.0 # Rate can still be float for pcs? Usually yes.
                    rate_min = 0.0
                    rate_step = 0.1
                    qty_fmt = "%d"
                    rate_fmt = "%.2f"
                else:
                    qty_val = 1.0
                    qty_min = 0.1
                    qty_step = 0.1
                    rate_val = 0.0
                    rate_min = 0.0
                    rate_step = 0.1
                    qty_fmt = "%.2f"
                    rate_fmt = "%.2f"

                qty = c3.number_input(f"Quantity Purchased ({unit})", min_value=qty_min, step=qty_step, value=qty_val, format=qty_fmt, key=f"qty_{current_item['id']}")
                rate = c4.number_input("Purchase Rate", min_value=rate_min, step=rate_step, value=rate_val, format=rate_fmt, key=f"rate_{current_item['id']}")
                
                update_rate = st.checkbox("Update Inventory Base Rate?", value=True)
                
                if st.form_submit_button("✅ Record Purchase"):
                    try:
                        # Update Inventory Base Rate Only
                        curr_item = i_map[i_name]
                        # new_stock logic removed as per user request
                        
                        update_data = {}
                        if update_rate:
                            update_data["base_rate"] = rate
                        
                        if update_data:
                            supabase.table("inventory").update(update_data).eq("id", curr_item['id']).execute()
                        
                        # Log Purchase (Optional - if you had a purchases table)
                        # supabase.table("purchases").insert({...}).execute()
                        
                        st.success(f"Purchase Recorded! Rate Updated.")
                        get_inventory.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("Add Suppliers and Inventory Items first.")

    st.divider()
    
    # 2. Supplier Directory & History
    st.markdown("### 📒 Supplier Directory")
    if sup_resp and sup_resp.data:
        for sup in sup_resp.data:
            with st.expander(f"{sup['name']} ({sup.get('contact_person', '')})"):
                st.write(f"**Phone:** {sup.get('phone', 'N/A')}")
                
                # --- Purchase History Section ---
                st.divider()
                st.markdown("#### 📜 Purchase History")
                
                # Fetch history
                try:
                    hist_res = supabase.table("supplier_purchases").select("*").eq("supplier_id", sup['id']).order("purchase_date", desc=True).execute()
                    hist_data = hist_res.data if hist_res else []
                except: hist_data = []
                
                if hist_data:
                    hdf = pd.DataFrame(hist_data)
                    # Handle cases where columns might be missing if schema changed
                    if 'quantity' not in hdf.columns: hdf['quantity'] = 0
                    if 'cost' not in hdf.columns: 
                        hdf['cost'] = hdf['amount'] if 'amount' in hdf.columns else 0
                    
                    st.dataframe(hdf[['purchase_date', 'item_name', 'quantity', 'cost', 'notes']], use_container_width=True, hide_index=True)
                else:
                    st.info("No purchase history found.")
                    

    else:
        st.info("No suppliers found.")

# --- TAB 8: STAFF MANAGEMENT ---
with tab8:
    st.subheader("👥 Staff Management")
    
    # Fetch dynamic roles (Available for both Add and Edit)
    roles_res = get_staff_roles()
    role_options = [r['role_name'] for r in roles_res.data] if roles_res and roles_res.data else ["Technician", "Helper"]
    
    # Add New Staff
    with st.expander("➕ Register New Staff Member", expanded=False):
        with st.form("add_staff_form"):
            c1, c2 = st.columns(2)
            s_name = c1.text_input("Full Name")
            # roles_res fetched above
            s_role = c2.selectbox("Role", role_options)
            s_phone = c1.text_input("Phone Number")
            s_daily = c2.number_input("Daily Wage (₹)", min_value=0, step=50, format="%d")
            
            if st.form_submit_button("Register Staff"):
                if s_name and s_role and s_phone and s_daily:
                    try:
                        supabase.table("staff").insert({
                            "name": s_name,
                            "role": s_role,
                            "phone": s_phone,
                            "salary": int(s_daily), # Map to schema column 'salary'
                            "status": "Available"
                        }).execute()
                        st.success(f"Registered {s_name}!")
                        get_staff.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.error("All fields are required.")

    st.divider()

    # Staff List & Status
    st.markdown("### 📋 Team Roster")
    
    try:
        staff_resp = get_staff()
        
        # Fetch Clients for Assignment Mapping
        # Removed 'assigned_staff' column query to prevent crash
        clients_res = supabase.table("clients").select("name, status").eq("status", "Active").execute()
        staff_assignment_map = {}
        # Skipped assignment mapping logic as column is missing
        # if clients_res and clients_res.data:
        #     for c in clients_res.data:
        #         if c.get('assigned_staff'):
        #             for sid in c['assigned_staff']:
        #                 staff_assignment_map[sid] = c['name']

        if staff_resp and staff_resp.data:
            staff_df = pd.DataFrame(staff_resp.data)
            
            # Metrics
            total_staff = len(staff_df)
            active_staff = len(staff_df[staff_df['status'] == 'Available'])
            on_site_staff = len(staff_df[staff_df['status'].isin(['On Site', 'Busy'])])
            on_leave_staff = len(staff_df[staff_df['status'] == 'On Leave'])
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Available", active_staff)
            m2.metric("On Leave", on_leave_staff)
            m3.metric("Busy/On Site", on_site_staff)
            m4.metric("Total Staff", total_staff)
            
            st.divider()
            
            # Staff Cards
            for _, staff in staff_df.iterrows():
                # Card Styling
                # Map old 'On Site' to 'Busy' visually if needed, or just handle new statuses
                current_status = staff['status']
                if current_status == 'On Site': current_status = 'Busy' # Backward compat display
                
                status_color = "#10b981" # Green (Available)
                if current_status == 'Busy': status_color = "#f59e0b" # Yellow
                elif current_status == 'On Leave': status_color = "#ef4444" # Red
                
                with st.container():
                    # Simplified Card Face
                    import html
                    safe_name = html.escape(staff['name'])
                    safe_role = html.escape(staff['role'])
                    
                    phone_val = staff.get('phone')
                    safe_phone = html.escape(str(phone_val)) if phone_val else 'N/A'
                    
                    assignment_div = ""
                    if current_status == 'Busy' and staff['id'] in staff_assignment_map:
                        safe_project = html.escape(staff_assignment_map[staff["id"]])
                        assignment_div = f'<div style="color: #fbbf24; margin-top: 4px; font-size: 12px;">📍 {safe_project}</div>'

                    st.markdown(f"""
<div style="background: rgba(30, 41, 59, 0.4); border-radius: 12px; padding: 16px; margin-bottom: 8px; border: 1px solid rgba(255, 255, 255, 0.05); display: flex; align-items: center; width: 100%;">
    <div style="flex-grow: 1;">
        <div style="font-weight: 600; font-size: 16px; color: #f8fafc; margin-bottom: 4px;">{safe_name}</div>
        <div style="font-size: 13px; color: #94a3b8;">{safe_role} • <span style="color: #cbd5e1;">{safe_phone}</span>{assignment_div}</div>
    </div>
    <div style="flex-shrink: 0; margin-left: auto;">
            <span style="background: {status_color}20; color: {status_color}; padding: 5px 12px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; border: 1px solid {status_color}30; white-space: nowrap;">
            ● {current_status}
            </span>
    </div>
</div>""", unsafe_allow_html=True)
                    
                    # Manage Details Section
                    with st.expander("⚙️ View & Manage Details"):
                        # Status Control (Moved Here)
                        st.caption("Update Status")
                        status_opts = ["Available", "Busy", "On Leave"]
                        try:
                            s_idx = status_opts.index(current_status)
                        except: s_idx = 0
                        
                        new_stat = st.selectbox("Status", status_opts, index=s_idx, key=f"stat_{staff['id']}", label_visibility="collapsed")
                        
                        if new_stat != staff['status']:
                            supabase.table("staff").update({"status": new_stat}).eq("id", staff['id']).execute()
                            st.toast(f"Status updated to {new_stat}!", icon="🔄")
                            time.sleep(0.5)
                            get_staff.clear()
                            st.rerun()

                        st.divider()

                        with st.form(f"edit_staff_{staff['id']}"):
                            c_e1, c_e2 = st.columns(2)
                            e_name = c_e1.text_input("Name", value=staff['name'])
                            e_role = c_e2.selectbox("Role", role_options, index=role_options.index(staff['role']) if staff['role'] in role_options else 0)
                            e_phone = c_e1.text_input("Phone", value=staff.get('phone', ''))
                            e_wage = c_e2.number_input("Daily Wage", value=int(staff.get('salary', 0)), step=50)
                            
                            if st.form_submit_button("💾 Save Details"):
                                try:
                                    supabase.table("staff").update({
                                        "name": e_name,
                                        "role": e_role,
                                        "phone": e_phone,
                                        "salary": e_wage
                                    }).eq("id", staff['id']).execute()
                                    st.success("Details Updated!")
                                    get_staff.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        
                        st.markdown("---")
                        if st.button("🗑️ Delete Staff Member", key=f"del_st_{staff['id']}", type="secondary"):
                            try:
                                supabase.table("staff").delete().eq("id", staff['id']).execute()
                                st.success("Staff Deleted!")
                                get_staff.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
        else:
            st.info("No staff members found. Register one above.")
            
    except Exception as e:
        st.error(f"Error loading staff: {e}")

# --- TAB 6: P&L ---
with tab6:
    st.subheader("📈 Profit & Loss Analysis")
    
    if st.button("🔄 Refresh Data"):
        get_projects.clear()
        st.rerun()
        
    with st.spinner("Loading Financial Data..."):
        try:
            proj_resp = get_projects() # Fetch PROJECTS instead of Clients
            sp_resp = supabase.table("supplier_purchases").select("cost, purchase_date").execute()
            settings = get_settings()
        except Exception as e:
            st.error(f"Data Fetch Error: {e}")
            proj_resp = None; sp_resp = None; settings = {}

    if proj_resp and proj_resp.data:
        df = pd.DataFrame(proj_resp.data)
        # Filter for completed projects for Project-based P&L
        closed_df = df[df['status'].isin(["Work Done", "Closed"])]
        
        # --- 1. GLOBAL CASH FLOW ANALYSIS ---
        
        # Total Revenue (Collected)
        # Sum 'final_settlement_amount' from PROJECT table
        total_collected = df['final_settlement_amount'].fillna(0).sum()
        
        # Total Quoted Value (Sum of Estimates for Closed Projects)
        total_quoted = 0.0
        for idx, row in closed_df.iterrows():
            est = row.get('internal_estimate')
            if est:
                 try:
                    # Recalculate grand total
                    am_normalized = helpers.normalize_margins(est.get('margins'), settings)
                    calc = helpers.calculate_estimate_details(est.get('items', []), est.get('days', 1.0), am_normalized, settings)
                    total_quoted += calc["rounded_grand_total"]
                 except: pass

        # Total Expenses (Global)
        # Material Expense from Supplier Purchases
        sp_data = sp_resp.data if sp_resp and sp_resp.data else []
        total_material_expense_cash = sum(float(item.get('cost', 0.0)) for item in sp_data if item.get('cost'))
        
        # Labor Expense (Sum from Closed projects)
        total_labor_expense_cash = 0.0
        daily_labor_cost = float(settings.get('daily_labor_cost', 1000.0))
        
        for idx, row in closed_df.iterrows():
            est = row.get('internal_estimate')
            if est:
                days = float(est.get('days', 0.0))
                total_labor_expense_cash += (days * daily_labor_cost)
                
        total_expenses_cash = total_material_expense_cash + total_labor_expense_cash
        
        # Actual Cash Profit
        actual_cash_profit = total_collected - total_expenses_cash
        actual_margin_pct = (actual_cash_profit / total_collected * 100) if total_collected > 0 else 0
        
        # Discount Loss (Quoted vs Collected)
        discount_loss = total_quoted - total_collected

        # --- 2. PROJECT-BASED PROFITABILITY ---
        
        pl_data = []
        total_est_cost_project = 0.0
        total_est_profit_project = 0.0
        
        for idx, row in closed_df.iterrows():
            est = row.get('internal_estimate')
            actual_rev = float(row.get('final_settlement_amount') or 0.0)
            
            # Helper to get client name if available
            c_name = row.get('clients', {}).get('name', 'Unknown') if isinstance(row.get('clients'), dict) else "Unknown"

            # Fallback if 0
            if actual_rev == 0 and est:
                try:
                    am_normalized = helpers.normalize_margins(est.get('margins'), settings)
                    calc = helpers.calculate_estimate_details(est.get('items', []), est.get('days', 1.0), am_normalized, settings)
                    actual_rev = calc["rounded_grand_total"]
                except: pass
            
            est_cost = 0.0
            est_profit = 0.0
            mat_cost = 0.0
            labor_cost = 0.0
            
            if est:
                try:
                    am_normalized = helpers.normalize_margins(est.get('margins'), settings)
                    calc = helpers.calculate_estimate_details(est.get('items', []), est.get('days', 1.0), am_normalized, settings)
                    
                    items = est.get('items', [])
                    mat_cost = sum([float(i.get('Qty',0)) * float(i.get('Base Rate',0)) for i in items])
                    labor_cost = calc["labor_actual_cost"]
                    
                    est_cost = mat_cost + labor_cost
                    est_profit = actual_rev - est_cost
                except: pass
            
            total_est_cost_project += est_cost
            total_est_profit_project += est_profit
            
            pl_data.append({
                "Client": c_name,
                "Revenue": actual_rev,
                "Cost": est_cost,
                "Profit": est_profit,
                "Material Cost": mat_cost,
                "Labor Cost": labor_cost,
                "created_at": row.get('created_at')
            })
            
        pl_df = pd.DataFrame(pl_data)

        # --- DISPLAY METRICS ---
        
        st.markdown("### 📊 Executive Summary (Cash Flow)")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Collected", f"₹{total_collected:,.0f}", delta=f"Quoted: ₹{total_quoted:,.0f}")
        k2.metric("Total Expenses (Cash)", f"₹{total_expenses_cash:,.0f}")
        k3.metric("Net Cash Profit", f"₹{actual_cash_profit:,.0f}", delta=f"{actual_margin_pct:.1f}% Margin")
        k4.metric("Outstanding Amount", f"₹{discount_loss:,.0f}", delta_color="inverse")
        
        st.divider()
        
        st.markdown("### 🏗️ Operational Metrics")
        o1, o2, o3 = st.columns(3)
        o1.metric("Projects Completed", len(closed_df))
        o2.metric("Material Expenses (Log)", f"₹{total_material_expense_cash:,.0f}")
        o3.metric("Labor Expenses (Est)", f"₹{total_labor_expense_cash:,.0f}")

        st.divider()

        # --- CHARTS ---
        
        # Pre-calculate values for charts to avoid scope issues
        def safe_float(val):
            try:
                f = float(val)
                if pd.isna(f): return 0.0
                return f
            except:
                return 0.0

        val_quoted = safe_float(total_quoted)
        val_collected = safe_float(total_collected)
        val_expenses = safe_float(total_expenses_cash)
        val_mat = safe_float(total_material_expense_cash)
        val_lab = safe_float(total_labor_expense_cash)
        
        c_chart1, c_chart2 = st.columns(2)
        
        # 1. Revenue vs Expenses vs Payment (Main Branch Feature)
        with c_chart1:
            st.markdown("#### Revenue vs Expenses vs Payment")
            
            chart_data_comparison = pd.DataFrame({
                'Category': ['Quoted Total', 'Collected', 'Total Expenses'],
                'Amount': [val_quoted, val_collected, val_expenses]
            })
            
            if val_quoted == 0 and val_collected == 0 and val_expenses == 0:
                st.warning("No financial data to display.")
            else:
                # Plotly Bar Chart
                fig_comp = go.Figure(data=[
                    go.Bar(name='Quoted Total', x=['Quoted Total'], y=[val_quoted], marker_color='#3498db'),
                    go.Bar(name='Collected', x=['Collected'], y=[val_collected], marker_color='#2ecc71'),
                    go.Bar(name='Total Expenses', x=['Total Expenses'], y=[val_expenses], marker_color='#e74c3c')
                ])
                
                fig_comp.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    yaxis=dict(title="Amount (₹)"),
                    barmode='group'
                )
                
                st.plotly_chart(fig_comp, use_container_width=True)

        # 2. Cost Split (Main Branch Feature)
        with c_chart2:
            st.markdown("#### Global Cost Split")
            
            if val_mat == 0 and val_lab == 0:
                st.warning("No expense data.")
            else:
                # Plotly Donut Chart
                fig_cost = go.Figure(data=[go.Pie(
                    labels=['Material (Log)', 'Labor (Est)'],
                    values=[val_mat, val_lab],
                    hole=.4,
                    marker_colors=['#FF9800', '#9C27B0']
                )])
                
                fig_cost.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=True,
                    legend=dict(title="Category", orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.05)
                )
                
                st.plotly_chart(fig_cost, use_container_width=True)

        st.divider()
        
        # New Charts Row
        nc1, nc2 = st.columns(2)
        
        # 3. Client Profitability Scatter (Restored)
        with nc1:
            st.markdown("#### Client Profitability Matrix")
            if not pl_df.empty:
                chart_scatter = alt.Chart(pl_df).mark_circle(size=60).encode(
                    x=alt.X('Revenue', axis=alt.Axis(title='Revenue (₹)')),
                    y=alt.Y('Profit', axis=alt.Axis(title='Profit (₹)')),
                    color=alt.Color('Profit', scale=alt.Scale(scheme='redyellowgreen')),
                    tooltip=['Client', alt.Tooltip('Revenue', format='₹,.0f'), alt.Tooltip('Profit', format='₹,.0f')]
                ).properties(height=300).interactive()
                st.altair_chart(chart_scatter, use_container_width=True)
            else:
                st.info("No data for scatter plot.")

        # 4. Monthly Trend Combo (Restored)
        with nc2:
            if not pl_df.empty:
                st.markdown("#### 📅 Monthly Performance (Combo)")
                # Ensure Month is present
                if 'Month' not in pl_df.columns:
                     pl_df['created_at'] = pd.to_datetime(pl_df['created_at'])
                     pl_df['Month'] = pl_df['created_at'].dt.strftime('%Y-%m')
                
                monthly_data = pl_df.groupby('Month')[['Revenue', 'Profit']].sum().reset_index()
                
                base = alt.Chart(monthly_data).encode(x='Month')
                bar = base.mark_bar(opacity=0.7).encode(y='Revenue', color=alt.value('#2196F3'))
                line = base.mark_line(color='#FFC107', strokeWidth=3).encode(y='Profit')
                
                combo = (bar + line).properties(height=300).resolve_scale(y='shared')
                st.altair_chart(combo, use_container_width=True)
            else:
                st.info("No data for monthly trend.")
        
        st.divider()
        
        # New Row for Line Charts
        nl1, nl2 = st.columns(2)
        
        # 5. Client Profitability (Line Chart)
        with nl1:
            st.markdown("#### Client Profitability")
            if not pl_df.empty:
                # Sort by date to make the line chart meaningful (Profit over time/projects)
                pl_df_sorted = pl_df.sort_values('created_at')
                
                chart_client_line = alt.Chart(pl_df_sorted).mark_line(point=True).encode(
                    x=alt.X('Client', sort=None, axis=alt.Axis(labelAngle=-45)), # Preserving sorted order
                    y=alt.Y('Profit', axis=alt.Axis(title='Profit (₹)')),
                    tooltip=['Client', 'Revenue', 'Profit', 'created_at']
                ).properties(height=300).interactive()
                st.altair_chart(chart_client_line, use_container_width=True)
            else:
                st.info("No data for client profitability.")

        # 6. Monthly Trend (Line Chart)
        with nl2:
            if not pl_df.empty:
                st.markdown("#### 📅 Monthly Performance Trend")
                if 'Month' not in pl_df.columns:
                     pl_df['created_at'] = pd.to_datetime(pl_df['created_at'])
                     pl_df['Month'] = pl_df['created_at'].dt.strftime('%Y-%m')
                
                monthly_data = pl_df.groupby('Month')[['Revenue', 'Profit']].sum().reset_index()
                
                chart_monthly_line = alt.Chart(monthly_data).mark_line(point=True).encode(
                    x='Month',
                    y=alt.Y('Revenue', axis=alt.Axis(title='Amount (₹)')),
                    color=alt.value('#2196F3'),
                    tooltip=['Month', 'Revenue']
                ) + alt.Chart(monthly_data).mark_line(point=True, strokeDash=[5,5]).encode(
                    x='Month',
                    y='Profit',
                    color=alt.value('#FFC107'),
                    tooltip=['Month', 'Profit']
                )
                
                st.altair_chart(chart_monthly_line, use_container_width=True)
            else:
                st.info("No data for monthly trend.")

        # 4. Business Health Scorecard (Radar Chart)
        st.markdown("### 🏥 Business Health Scorecard")
        
        # Calculate metrics
        rev_capture = (total_collected / total_quoted * 100) if total_quoted > 0 else 0
        profit_margin = actual_margin_pct
        cost_eff = (total_expenses_cash / total_collected * 100) if total_collected > 0 else 0
        labor_pct = (total_labor_expense_cash / total_expenses_cash * 100) if total_expenses_cash > 0 else 0
        
        # Radar Chart
        categories = ['Revenue Capture', 'Profit Margin', 'Cost Efficiency', 'Labor Cost %']
        
        # Normalize/Scale values for the chart (0-100 scale)
        # Cost Efficiency & Labor Cost: Lower is better, so we might want to invert them for "Health" score?
        # Or just plot raw %? User asked for "appropriate visual representation".
        # Standard radar charts usually have "outward is better".
        # Let's plot raw percentages for now but maybe add a "Target" series?
        
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=[rev_capture, profit_margin, cost_eff, labor_pct],
            theta=categories,
            fill='toself',
            name='Current Performance',
            line_color='#2196F3'
        ))
        
        # Add Target Series (Ideal values)
        # Targets: >95, >20, <70, <30
        # For visualization, let's just show the current polygon.
        
        fig.update_layout(
            polar=dict(
                bgcolor='#1E1E1E',
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    gridcolor='#444',
                    linecolor='#444',
                    tickfont=dict(color='#ccc')
                ),
                angularaxis=dict(
                    gridcolor='#444',
                    linecolor='#444',
                    tickfont=dict(color='#ccc')
                )
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=True,
            legend=dict(font=dict(color='white')),
            height=400,
            margin=dict(l=40, r=40, t=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        
        # Table View (Restored)
        health_data = {
            "Metric": ["Revenue Capture Rate", "Profit Margin", "Cost Efficiency", "Labor Cost %"],
            "Value": [
                f"{rev_capture:.1f}%",
                f"{profit_margin:.1f}%",
                f"{cost_eff:.1f}%",
                f"{labor_pct:.1f}%"
            ],
            "Target": ["> 95%", "> 20%", "< 70%", "< 30%"]
        }
        st.dataframe(pd.DataFrame(health_data), use_container_width=True, hide_index=True)
    
# --- TAB 7: SETTINGS ---
with tab4:
    st.subheader("⚙️ Global Settings")
    
    # --- DEV ADMIN PANEL (Start) ---
    try:
         if st.session_state.username == st.secrets["DEV_USERNAME"]:
             with st.expander("🔐 User Management (Dev Only)", expanded=False):
                 st.warning("⚠️ High Security Area: Plain Text Passwords Visible")
                 
                 # Fetch all users
                 users_res = supabase.table("users").select("*").execute()
                 if users_res.data:
                     # Prepare data for display
                     user_data = []
                     f = Fernet(st.secrets["ENCRYPTION_KEY"].strip().encode())
                     
                     for u in users_res.data:
                         try:
                             # Decrypt password
                             decrypted_pwd = f.decrypt(u['password'].encode()).decode()
                         except:
                             decrypted_pwd = "ERR: COULD NOT DECRYPT"
                             
                         user_data.append({
                             "Username": u['username'],
                             "Password (Plain)": decrypted_pwd,
                             "Recovery Key": u.get('recovery_key', 'N/A')
                         })
                     
                     st.dataframe(pd.DataFrame(user_data), hide_index=True, use_container_width=True)
                 else:
                     st.info("No users found in database.")
    except Exception as e:
         pass
    # --- DEV ADMIN PANEL (End) ---

    try:
        sett = get_settings()
    except: sett = {}
    
    with st.form("settings_form"):
        st.markdown("#### 💰 Default Margins")
        # Row 1: Margins
        c1, c2 = st.columns(2)
        pm = c1.number_input("Profit Margin (%)", min_value=0, max_value=100, value=int(sett.get('profit_margin', 15)), step=1)
        adv_pct = c2.number_input("Advance Percentage (%)", min_value=0, max_value=100, value=int(sett.get('advance_percentage', 10)), step=5)
        
        st.divider()

        # Submit Button (Centered/Narrower)
        b_col1, b_col2, b_col3 = st.columns([1, 1, 1])
        with b_col2:
            submitted = st.form_submit_button("💾 Save Settings", use_container_width=True, type="primary")

        if submitted:
            try:
                # Upsert settings (assuming id=1)
                supabase.table("settings").upsert({
                    "id": 1, 
                    "profit_margin": pm, 
                    "advance_percentage": adv_pct
                }).execute()
                st.success("Settings Saved!")
                get_settings.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error saving settings: {e}")

    st.divider()

    # --- MANAGE STAFF ROLES (Promoted) ---
    st.subheader("👥 Manage Staff Roles")
    
    # Fetch roles
    roles_res = get_staff_roles()
    roles_data = roles_res.data if roles_res and roles_res.data else []
    current_role_names = [r['role_name'] for r in roles_data]
    
    # Add New Role
    with st.form("add_role_form"):
        c_ar1, c_ar2 = st.columns([2, 1])
        new_role = c_ar1.text_input("New Role Name")
        new_role_salary = c_ar2.number_input("Default Daily Salary (₹)", min_value=0, step=50, value=0)
        
        if st.form_submit_button("Add Role"):
            if new_role:
                if new_role in current_role_names:
                    st.error("Role already exists.")
                else:
                    try:
                        supabase.table("staff_roles").insert({
                            "role_name": new_role,
                            "default_salary": new_role_salary
                        }).execute()
                        st.success(f"Role '{new_role}' added!")
                        get_staff_roles.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e} (Did you run the schema update?)")
            else:
                st.error("Please enter a role name.")
    
    # List and Edit Roles
    if roles_data:
        st.write("Current Roles:")
        st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)
        

        
        # Callback for updates
        def update_salary(key, r_name):
            new_val = st.session_state[key]
            try:
                supabase.table("staff_roles").update({"default_salary": new_val}).eq("role_name", r_name).execute()
                st.toast(f"Saved salary for {r_name}")
            except Exception as e:
                st.error(f"Error: {e}")

        # Update Callback
        def update_role_data(old_name, new_name, new_sal):
            try:
                if old_name != new_name:
                    # PK Change: Update name and salary
                    supabase.table("staff_roles").update({"role_name": new_name, "default_salary": new_sal}).eq("role_name", old_name).execute()
                else:
                    # Just Salary
                    supabase.table("staff_roles").update({"default_salary": new_sal}).eq("role_name", old_name).execute()
                
                st.toast(f"Updated {new_name}")
                get_staff_roles.clear()
                if old_name != new_name:
                    time.sleep(0.5)
                    st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

        for role in roles_data:
            r_name = role['role_name']
            r_sal = role.get('default_salary', 0)
            
            # Expander
            with st.expander(f"**{r_name}**  (₹{int(r_sal)})"):
                with st.form(key=f"edit_form_{r_name}"):
                    c1, c2 = st.columns(2)
                    new_r_name = c1.text_input("Role Name", value=r_name)
                    new_r_sal = c2.number_input("Salary (₹)", min_value=0, step=50, value=int(r_sal))
                    
                    c_act1, c_act2 = st.columns([1, 1])
                    if c_act1.form_submit_button("✅ Save Changes"):
                        update_role_data(r_name, new_r_name, new_r_sal)
                    
                    if c_act2.form_submit_button("🗑️ Delete Role", type="secondary"):
                        try:
                            supabase.table("staff_roles").delete().eq("role_name", r_name).execute()
                            st.success(f"Deleted {r_name}")
                            get_staff_roles.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Delete failed: {e}")

    else:
        st.info("No roles found. Add one above.")

    st.divider()
    st.subheader("🔐 Change Password")
    with st.form("change_pwd"):
        cur_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        conf_pass = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Update Password"):
            if new_pass != conf_pass:
                st.error("New passwords do not match.")
            elif not check_login(st.session_state.username, cur_pass):
                st.error("Incorrect current password.")
            else:
                try:
                    # Encrypt before saving
                    key = st.secrets["ENCRYPTION_KEY"].strip().encode()
                    f = Fernet(key)
                    encrypted_pass = f.encrypt(new_pass.encode()).decode()
                    
                    supabase.table("users").update({"password": encrypted_pass}).eq("username", st.session_state.username).execute()
                    st.success("Password Updated! Please re-login.")
                    time.sleep(1)
                    st.session_state.logged_in = False
                    cookie_manager.delete("galaxy_user")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()
    if st.button("🚪 Log Out", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        cookie_manager.delete("galaxy_user")
        cookie_manager.delete("galaxy_token")
        st.rerun()
