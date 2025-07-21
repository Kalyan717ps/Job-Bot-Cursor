import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException

# ✅ UPDATE THESE
YOUR_NAME = "Punna Sudha Kalyan"
YOUR_EMAIL = "punnasudhakalyan@gmail.com"
YOUR_RESUME_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Resume\PUNNA_SUDHA_KALYAN_RESUME.pdf"
CHROMEDRIVER_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job-Bot-Cursor\chromedriver-win64\chromedriver.exe"

def apply_to_job(job_url):
    print(f"🔗 Applying to job: {job_url}")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Optional headless
    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.get(job_url)
    time.sleep(5)

    try:
        if "accounts.google.com" in driver.current_url:
            print("Google Sign-In required")
            driver.quit()
            sys.exit(2)

        if "login" in driver.current_url or "signin" in driver.current_url:
            print("Login required")
            driver.quit()
            sys.exit(2)

        # Simulate applying
        name_field = driver.find_element("name", "name")
        name_field.send_keys(YOUR_NAME)
        print("✅ Form found and filled.")
        driver.quit()
        sys.exit(0)

    except NoSuchElementException:
        print("No application form found")
        driver.quit()
        sys.exit(2)
    except Exception as e:
        print("Unknown error or unsupported apply process")
        driver.quit()
        sys.exit(2)

if __name__ == "__main__":
    apply_to_job(sys.argv[1]) 