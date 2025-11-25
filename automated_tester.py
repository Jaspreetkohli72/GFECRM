import time
from playwright.sync_api import sync_playwright
import os

# CONFIGURATION
APP_URL = "https://jugnoocrm.streamlit.app/"
USERNAME = "Jaspreet"
PASSWORD = "CRMJugnoo@123"
REPORT_FILE = "full_test_report.html"

results = []

def log_result(test_name, status, message=""):
    color = "#4ade80" if status == "PASS" else "#f87171"
    results.append(f"<tr style='color:{color}; border-bottom: 1px solid #333;'><td>{test_name}</td><td><b>{status}</b></td><td>{message}</td></tr>")
    print(f"[{status}] {test_name}: {message}")

def run_tests():
    print(f"🚀 STARTING COMPREHENSIVE TEST SUITE ON: {APP_URL}")
    
    with sync_playwright() as p:
        # Grant geolocation permissions for the GPS test
        browser = p.chromium.launch(headless=False, slow_mo=1500)
        context = browser.new_context(permissions=['geolocation'], geolocation={'latitude': 28.6139, 'longitude': 77.2090})
        page = context.new_page()
        
        try:
            # ---------------------------------------------------------
            # PHASE 1: LOAD & LOGIN
            # ---------------------------------------------------------
            print("Phase 1: Initialization & Login...")
            page.goto(APP_URL, timeout=180000)
            
            # Wake up handling
            try:
                wake_btn = page.get_by_text("Yes, get this app back up!")
                if wake_btn.is_visible(timeout=5000):
                    print("💤 Waking up app...")
                    wake_btn.click()
                    time.sleep(30)
            except: pass

            # Locate Iframe
            iframe = page.frame_locator('iframe[title="streamlitApp"]')
            iframe.get_by_role("textbox", name="Username").wait_for(timeout=120000)
            
            # Login
            iframe.get_by_role("textbox", name="Username").fill(USERNAME)
            iframe.get_by_role("textbox", name="Password").fill(PASSWORD)
            iframe.get_by_role("button", name="Login").click()
            
            # Verify Dashboard Load
            iframe.get_by_text("Active Projects").wait_for(timeout=60000)
            log_result("Authentication", "PASS", "Login successful & Dashboard loaded")

            # ---------------------------------------------------------
            # PHASE 2: SETTINGS & INVENTORY (Add Item)
            # ---------------------------------------------------------
            print("Phase 2: Settings & Inventory...")
            # Switch Tab
            iframe.get_by_role("tab", name="Settings").click()
            
            # Verify Sliders Exist
            iframe.locator("div[data-testid='stSlider']").first.wait_for(state="visible", timeout=30000)
            if iframe.locator("div[data-testid='stSlider']").count() >= 3:
                log_result("Settings UI", "PASS", "Profit Margin Sliders detected")
            else:
                log_result("Settings UI", "FAIL", "Profit Sliders missing")

            # Add Inventory Item
            test_item_name = f"Test_Item_{int(time.time())}"
            iframe.get_by_label("Item Name").fill(test_item_name)
            iframe.get_by_label("Rate").fill("500")
            iframe.get_by_role("button", name="Add Item").click()
            
            # Verify Table Update by waiting for the text to appear
            iframe.get_by_text(test_item_name).wait_for(state="visible", timeout=30000)
            log_result("Inventory CRUD", "PASS", f"Added item '{test_item_name}'")

            # ---------------------------------------------------------
            # PHASE 3: NEW CLIENT (Create & GPS)
            # ---------------------------------------------------------
            print("Phase 3: Create Client...")
            iframe.get_by_role("tab", name="New Client").click()
            iframe.get_by_label("Client Name").wait_for(state="visible", timeout=30000)
            
            # Test GPS Button
            if iframe.get_by_text("Get Current Location").is_visible():
                iframe.get_by_text("Get Current Location").click()
                iframe.get_by_text("Location Captured").wait_for(timeout=15000)
                log_result("GPS Function", "PASS", "Geolocation captured successfully")
            
            # Create Client
            client_name = "TEST_BOT_CLIENT"
            iframe.get_by_label("Client Name").fill(client_name)
            iframe.get_by_label("Phone Number").fill("9999999999")
            iframe.get_by_label("Address").fill("123 Automated Test Lane")
            iframe.get_by_role("button", name="Create Client").click()
            
            # Wait for success message
            iframe.get_by_text(f"Client {client_name} Added!").wait_for()
            log_result("Client CRUD", "PASS", "Client created successfully")

            # ---------------------------------------------------------
            # PHASE 4: ESTIMATOR (Generate Quote)
            # ---------------------------------------------------------
            print("Phase 4: Estimator Engine...")
            iframe.get_by_role("tab", name="Estimator").click()
            
            # Wait for the