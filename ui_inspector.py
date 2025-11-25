from playwright.sync_api import sync_playwright
import time

APP_URL = "https://jugnoocrm.streamlit.app/"
USERNAME = "Jaspreet"
PASSWORD = "CRMJugnoo@123"
OUTPUT_FILE = "selectors_log.txt"

def analyze_page(page, file_handle, section_name, iframe_context):
    print(f"Scanning {section_name}...")
    file_handle.write(f"\n--- {section_name} ---\n")
    
    # 1. ANALYZE INPUTS
    inputs = iframe_context.locator("input, textarea").all()
    if inputs:
        file_handle.write("\n[INPUTS]\n")
        for i, el in enumerate(inputs):
            if not el.is_visible(): continue
            
            # Grab useful attributes
            lbl = el.get_attribute("aria-label") or "No Label"
            val = el.input_value()
            id_val = el.get_attribute("id") or "No ID"
            
            # Recommend the best selector
            best_selector = f'iframe.get_by_label("{lbl}")' if lbl != "No Label" else f'iframe.locator("#{id_val}")'
            
            file_handle.write(f"{i+1}. Label: '{lbl}' | ID: '{id_val}' | Current Value: '{val}'\n")
            file_handle.write(f"   Recommended Code: {best_selector}\n")

    # 2. ANALYZE BUTTONS
    buttons = iframe_context.locator("button").all()
    if buttons:
        file_handle.write("\n[BUTTONS]\n")
        for i, el in enumerate(buttons):
            if not el.is_visible(): continue
            
            text = el.inner_text().split('\n')[0].strip() # First line only
            if not text: continue
            
            kind = el.get_attribute("kind") or "generic"
            
            # Recommend selector
            best_selector = f'iframe.get_by_role("button", name="{text}")'
            
            file_handle.write(f"{i+1}. Text: '{text}' | Kind: {kind}\n")
            file_handle.write(f"   Recommended Code: {best_selector}\n")

    # 3. ANALYZE SELECTBOXES (Streamlit Specific)
    selects = iframe_context.locator("div[data-testid='stSelectbox']").all()
    if selects:
        file_handle.write("\n[DROPDOWNS / SELECTBOXES]\n")
        for i, el in enumerate(selects):
            if not el.is_visible(): continue
            
            try:
                label = el.locator("label").inner_text()
            except:
                label = "Unknown Label"
                
            best_selector = f'iframe.locator("div[data-testid=\'stSelectbox\']").nth({i}) # For \'{label}\''
            
            file_handle.write(f"{i+1}. Label: '{label}'\n")
            file_handle.write(f"   Recommended Code: {best_selector}\n")

def run_inspector():
    print(f"🕵️ STARTING UI INSPECTOR ON: {APP_URL}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Open File
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(f"UI INSPECTION REPORT - {time.ctime()}\n")
            f.write("="*50 + "\n")
            
            # --- LOGIN SCREEN ---
            page.goto(APP_URL, timeout=120000)
            print("Waiting for Login Screen...")
            
            # Wake up handler
            try:
                wake = page.get_by_text("Yes, get this app back up!")
                if wake.is_visible(timeout=5000):
                    wake.click()
                    time.sleep(20)
            except: pass

            # Locate Iframe
            print("Looking for Streamlit iframe...")
            iframe = page.frame_locator('iframe[title="streamlitApp"]')
            
            # Wait for inputs to settle
            iframe.get_by_role("textbox", name="Username").wait_for(timeout=60000)
            
            analyze_page(page, f, "LOGIN SCREEN", iframe)
            
            # Perform Login to see Dashboard
            print("Logging in to inspect Dashboard...")
            try:
                iframe.get_by_role("textbox", name="Username").fill(USERNAME)
                iframe.get_by_role("textbox", name="Password").fill(PASSWORD)
                iframe.get_by_role("button", name="Login").click()
                
                iframe.get_by_text("Active Projects").wait_for(timeout=60000)
                time.sleep(5) # Wait for dashboard widgets to render
                
                # Scan all tabs
                tabs = ["Dashboard", "New Client", "Estimator", "Settings"]
                for tab_name in tabs:
                    print(f"Inspecting Tab: {tab_name}...")
                    try:
                        iframe.get_by_role("tab", name=tab_name).click()
                        time.sleep(3) # Wait for tab to render
                        analyze_page(page, f, f"TAB: {tab_name.upper()}", iframe)
                    except Exception as e:
                        f.write(f"\n\n[ERROR] Could not inspect tab '{tab_name}': {e}")
                        print(f"Error inspecting tab {tab_name}: {e}")
                
            except Exception as e:
                f.write(f"\n\n[ERROR] Could not proceed past login: {e}")
                print(f"Error: {e}")

        browser.close()
        print(f"\n✅ Inspection Complete! Open '{OUTPUT_FILE}' to see the selectors.")

if __name__ == "__main__":
    run_inspector()
