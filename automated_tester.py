import time
from playwright.sync_api import sync_playwright
import os

# CONFIGURATION
APP_URL = "http://localhost:8501"
USERNAME = "Jaspreet"
PASSWORD = "CRMJugnoo@123"
REPORT_FILE = "test_report.html"

results = []

def log_result(test_name, status, message=""):
    color = "green" if status == "PASS" else "red"
    results.append(f"<tr style='color:{color}'><td>{test_name}</td><td><b>{status}</b></td><td>{message}</td></tr>")
    print(f"[{status}] {test_name}: {message}")

def run_tests():
    print(f"🚀 Starting UI Tests on {APP_URL}...")
    
    with sync_playwright() as p:
        # --- TEST 1: DESKTOP LOGIN ---
        try:
            browser = p.chromium.launch(headless=True) # Set to False to watch it happen
            page = browser.new_page()
            page.goto(APP_URL)
            
            # Wait for app to load
            page.wait_for_selector("input[aria-label='Username']", timeout=10000)
            
            # Perform Login
            page.fill("input[aria-label='Username']", USERNAME)
            page.fill("input[aria-label='Password']", PASSWORD)
            # Streamlit buttons are tricky, usually use text locator
            page.get_by_text("Login").click()
            
            # Wait for Dashboard
            page.wait_for_selector("text=Active Projects", timeout=10000)
            log_result("Desktop Login", "PASS", "Successfully logged in and reached Dashboard")
            
            # Check PDF Button
            if page.get_by_text("Download PDF").count() > 0:
                log_result("PDF Generation", "PASS", "PDF Download button is visible")
            else:
                log_result("PDF Generation", "WARNING", "No PDF button found (Client list might be empty)")

            # Check Navigate Button
            if page.get_by_text("Navigate to Site").count() > 0:
                log_result("Navigate Feature", "PASS", "Navigate button is visible")
            
            browser.close()
            
        except Exception as e:
            log_result("Desktop Login / Dashboard", "FAIL", str(e))

        # --- TEST 2: MOBILE VIEW (WHITE BARS CHECK) ---
        try:
            iphone = p.devices['iPhone 12']
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(**iphone)
            page = context.new_page()
            page.goto(APP_URL)
            
            # Check Login Screen Background (Should be dark #0E1117)
            # We check the computed style of the main app container
            bg_color = page.evaluate("window.getComputedStyle(document.querySelector('.stApp')).backgroundColor")
            
            # RGB for #0E1117 is rgb(14, 17, 23)
            if "14, 17, 23" in bg_color:
                log_result("Mobile UI (White Bars)", "PASS", "Background is Dark (#0E1117) on Mobile")
            else:
                log_result("Mobile UI (White Bars)", "FAIL", f"Background detected as {bg_color}")
            
            browser.close()
        except Exception as e:
            log_result("Mobile Simulation", "FAIL", str(e))

    # --- GENERATE REPORT ---
    with open(REPORT_FILE, "w") as f:
        f.write(f"""
        <html>
        <body style="font-family: Arial; background: #1e1e1e; color: white; padding: 20px;">
            <h1>🩺 CRM Test Report</h1>
            <p>Generated: {time.ctime()}</p>
            <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%;">
                <tr><th>Test Case</th><th>Status</th><th>Details</th></tr>
                {''.join(results)}
            </table>
        </body>
        </html>
        """)
    print(f"\n✅ Tests Complete. Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    run_tests()
