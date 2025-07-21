import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import sys

# ✅ Configure your personal details here
YOUR_NAME = "Punna Sudha Kalyan"
YOUR_EMAIL = "punnasudhakalyan@gmail.com"
YOUR_RESUME_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Resume\PUNNA_SUDHA_KALYAN_RESUME.pdf"

# Path to chromedriver
CHROMEDRIVER_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job-Bot-Cursor\chromedriver-win64\chromedriver.exe"

def apply_to_job(job_url):
    print(f"\U0001F517 Applying to job: {job_url}")

    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Optional for silent browser

    # Correct path to chromedriver.exe
    chrome_driver_path = CHROMEDRIVER_PATH
    service = Service(executable_path=chrome_driver_path)

    # Launch Chrome
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(job_url)
    time.sleep(5)

    print("\u2705 Browser loaded the page successfully.")

    # Attempt form fill here if available (we'll enhance later)
    try:
        name_field = driver.find_element("name", "name")
        name_field.send_keys(YOUR_NAME)
        print("✅ Filled name.")
    except Exception as e:
        print("⚠️ No apply button found. Opening main page.")
        print(f"⚠️ Could not auto-fill/apply this job: {e}")

    driver.quit()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_link = sys.argv[1]
        apply_to_job(job_link)
    else:
        print("No job URL provided.") 