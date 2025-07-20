# scrape_jobs.py - Job scraping helper script for Job Bot
import requests
from bs4 import BeautifulSoup
import csv

def scrape_and_save():
    url = "https://remoteok.com/remote-dev-jobs"  # Use a specific category page
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page. Status code: {response.status_code}")
        return 0

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    for row in soup.find_all("tr", class_="job"):
        title_elem = row.find("h2")
        company_elem = row.find("h3")
        link = row.get("data-href")

        if title_elem and company_elem and link:
            title = title_elem.get_text(strip=True)
            company = company_elem.get_text(strip=True)
            full_link = f"https://remoteok.com{link}"
            jobs.append({
                "title": title,
                "company": company,
                "link": full_link
            })

    # Save to CSV
    with open("remoteok_jobs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "company", "link"])
        writer.writeheader()
        writer.writerows(jobs)

    print(f"✅ Scraped and saved {len(jobs)} job(s) 🎉")
    return len(jobs)

if __name__ == "__main__":
    scrape_and_save()