import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

# ✅ Configure your personal details here
YOUR_NAME = "Punna Sudha Kalyan"
YOUR_EMAIL = "punnasudhakalyan@gmail.com"
YOUR_RESUME_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Resume\PUNNA_SUDHA_KALYAN_RESUME.pdf"

# Path to chromedriver
CHROMEDRIVER_PATH = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job Bot\chromedriver-win64\chromedriver.exe"

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
service = Service(executable_path=CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

# Load the CSV file with job links
with open("remoteok_jobs.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    jobs = list(reader)

# Applied jobs log
applied_jobs = []

# Loop through the jobs
for job in jobs:
    print(f"\n🔗 Opening: {job['title']} - {job['company']}")

    try:
        driver.get(job['link'])
        time.sleep(5)  # Wait for page to load (increase if needed)

        # Optional: try finding and clicking an "Apply" button
        try:
            apply_button = driver.find_element(By.PARTIAL_LINK_TEXT, "Apply")
            apply_button.click()
            time.sleep(3)
        except:
            print("⚠️ No apply button found. Opening main page.")

        # Look for form fields and fill them (basic form detection)
        try:
            driver.find_element(By.NAME, "name").send_keys(YOUR_NAME)
            driver.find_element(By.NAME, "email").send_keys(YOUR_EMAIL)
            resume_input = driver.find_element(By.XPATH, "//input[@type='file']")
            resume_input.send_keys(YOUR_RESUME_PATH)

            submit = driver.find_element(By.XPATH, '//button[contains(text(),"Submit") or contains(text(), "Apply")]')
            submit.click()

            print("✅ Applied successfully!")

            applied_jobs.append(job)

        except Exception as e:
            print("⚠️ Could not auto-fill/apply this job:", e)

    except Exception as e:
        print("🚫 Error opening job:", e)

# Quit browser
driver.quit()

# Save applied jobs for record
with open("applied_jobs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "company", "link"])
    writer.writeheader()
    writer.writerows(applied_jobs)

print(f"\n👍 Applied to {len(applied_jobs)} jobs.") 