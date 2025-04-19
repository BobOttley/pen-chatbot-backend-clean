# scrape_morehouse.py

import requests
from bs4 import BeautifulSoup
import json

# List of pages to scrape
URLS = [
    "https://www.morehouse.org.uk/",
    "https://www.morehouse.org.uk/admissions/our-open-events/",
    "https://www.morehouse.org.uk/our-school/meet-the-head/",
    "https://www.morehouse.org.uk/our-school/equity-diversity-and-inclusion-edi/",
    "https://www.morehouse.org.uk/our-school/our-ethos/",
    "https://www.morehouse.org.uk/beyond-the-classroom/faith-life/",
    "https://www.morehouse.org.uk/our-school/pastoral-care/",
    "https://www.morehouse.org.uk/our-school/more-house-stories/",
    "https://www.morehouse.org.uk/our-school/history/",
    "https://www.morehouse.org.uk/our-school/houses/",
    "https://www.morehouse.org.uk/pre-senior/",
    "https://www.morehouse.org.uk/learning/academic-life/",
    "https://www.morehouse.org.uk/learning/subjects/",
    "https://www.morehouse.org.uk/learning/sixth-form/",
    "https://www.morehouse.org.uk/learning/our-creative-suite/",
    "https://www.morehouse.org.uk/learning/be-more/",
    "https://www.morehouse.org.uk/learning/learning-support/",
    "https://www.morehouse.org.uk/learning/results-and-destinations/",
    "https://www.morehouse.org.uk/beyond-the-classroom/sport/",
    "https://www.morehouse.org.uk/beyond-the-classroom/co-curricular-programme/",
    "https://www.morehouse.org.uk/beyond-the-classroom/city-curriculum/",
    "https://www.morehouse.org.uk/partnerships/",
    "https://www.morehouse.org.uk/news-and-calendar/term-dates/",
    "https://www.morehouse.org.uk/information/safeguarding/",
    "https://www.morehouse.org.uk/information/school-uniform/",
    "https://www.morehouse.org.uk/information/lettings/",
    "https://www.morehouse.org.uk/information/school-lunches/",
    "https://www.morehouse.org.uk/information/our-staff-and-governors/",
    "https://www.morehouse.org.uk/information/school-policies/",
    "https://www.morehouse.org.uk/information/inspection-reports/",
    "https://www.morehouse.org.uk/contact/",
    "https://www.morehouse.org.uk/news-and-calendar/calendar/",
    "https://www.morehouse.org.uk/upcoming-events/"
]

all_paragraphs = []

for url in URLS:
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        continue

    soup = BeautifulSoup(res.text, "html.parser")
    # Narrow to the main content area (fallback to full page if no <main> tag)
    main = soup.select_one('main') or soup

    # Grab both paragraphs and list items within that area
    for tag in main.find_all(['p', 'li']):
        text = tag.get_text(strip=True)
        if text:
            all_paragraphs.append(text)

with open("morehouse_paragraphs.json", "w", encoding="utf-8") as f:
    json.dump(all_paragraphs, f, ensure_ascii=False, indent=2)

print(f"Extracted {len(all_paragraphs)} items into morehouse_paragraphs.json")

