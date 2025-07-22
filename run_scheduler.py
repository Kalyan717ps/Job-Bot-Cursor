import schedule
import time
import subprocess

def run_scraper():
    subprocess.run(['python', 'scrape_jobs.py'])

# Every 7 days (weekly)
schedule.every(7).days.do(run_scraper)
# Or: schedule.every().day.at("02:00").do(run_scraper)  # Uncomment to run daily at 2:00am

print("Job scraping scheduler started.")
while True:
    schedule.run_pending()
    time.sleep(60) 