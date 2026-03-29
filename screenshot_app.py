from playwright.sync_api import sync_playwright
import time

def capture_ui():
    with sync_playwright() as p:
        print("Launching headless Chromium...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        
        print("Connecting to Streamlit interface running on localhost...")
        try:
            page.goto("http://localhost:8501", timeout=30000)
        except Exception as e:
            print("Is Streamlit running? Could not connect...", e)
            return

        page.wait_for_selector(".stApp", state="visible")
        page.wait_for_timeout(3000) # Let the initial UI elements fully paint
        
        try:
            print("Inputting normal language test question into the AI Insight Tool...")
            # Streamlit ChatInput locator by aria-label
            text_area = page.locator('textarea[aria-label="E.g., Which region had the worst Cost Per Click?"]')
            text_area.fill("Which exact campaign had the absolute highest return on investment (ROI)?")
            page.wait_for_timeout(500)
            
            # Press enter to submit the query
            text_area.press("Enter")
            
            print("Waiting for the AI translation, database query, and response to display...")
            # Give the LLM and SQLite ample time to calculate the ROI, respond, and render the output dropdown
            page.wait_for_timeout(10000) 
            
        except Exception as e:
            print("Couldn't automate the interaction...", e)
            
        print("Taking stunning high-res screenshot of the output response!")
        page.screenshot(path="app_screenshot.png", full_page=True)
        
        browser.close()
        print("UI successfully captured to `app_screenshot.png`!")

if __name__ == "__main__":
    capture_ui()
