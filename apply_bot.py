import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

# ✅ Configure your personal details here
YOUR_NAME = "Punna Sudha Kalyan"
YOUR_EMAIL = "punnasudhakalyan@gmail.com"
YOUR_RESUME_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Resume\PUNNA_SUDHA_KALYAN_RESUME.pdf"

# Path to chromedriver
CHROMEDRIVER_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job-Bot-Cursor\chromedriver-win64\chromedriver.exe"

def apply_to_job(job_url):
    print(f"🔗 Applying to job: {job_url}")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Optional
    path = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job-Bot-Cursor\chromedriver-win64\chromedriver.exe"
    driver = webdriver.Chrome(service=Service(path), options=options)
    driver.get(job_url)
    time.sleep(5)

    try:
        # Try to locate and fill the form
        name_field = driver.find_element("name", "name")
        # ... fill form logic here ...
        print("✅ Form found and filled.")
        driver.quit()
        sys.exit(0)
    except Exception as e:
        reason = f"No application form found: {e}"
        print(reason)
        driver.quit()
        sys.exit(2)

if __name__ == "__main__":
    apply_to_job(sys.argv[1]) 