from selenium import webdriver
from selenium.webdriver.chrome.service import Service

path = r"C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job-Bot-Cursor\chromedriver-win64\chromedriver.exe"

options = webdriver.ChromeOptions()
service = Service(executable_path=path)
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.google.com")
print("✅ Google loaded!")
driver.quit()