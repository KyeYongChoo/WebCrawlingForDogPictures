"""A small, polite web crawler that downloads dog images from Wikimedia Commons.

How it works (the classic crawler loop):
    1. Start from a seed URL (a Commons category page for a breed).
    2. Fetch the HTML and parse it for links (each image's "File:" page).
    3. Visit each file page, find the actual image URL, and download it.
    4. Repeat for every breed until we have enough images.

Politeness rules built in: obey robots.txt, identify ourselves with a
User-Agent, and pause between requests.
"""

import csv
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

BASE = "https://commons.wikimedia.org"
# Wikimedia asks scrapers to use a descriptive User-Agent. Add contact info if you like.
USER_AGENT = "DogImageCrawlerLearningProject/1.0 (educational; python-requests)"
DELAY_SECONDS = 1.5  # pause between requests so we don't hammer the server
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")

# Breed name -> Commons category. 10 breeds x 10 images = 100 images.
BREEDS = {
    # Commons category names are inconsistent (some plural, some singular), so these
    # were checked by hand against the site.
    "labrador_retriever": "Labrador Retriever",
    "golden_retriever": "Golden Retriever",
    "german_shepherd": "German Shepherd Dog",
    "beagle": "Beagle (dog)",
    "bulldog": "Bulldog",
    "poodle": "Poodles",
    "dachshund": "Dachshund",
    "siberian_husky": "Siberian Husky",
    "pug": "Pug",
    "chihuahua": "Chihuahua (dog)",
}
IMAGES_PER_BREED = 10
OUTPUT_DIR = Path("dog_images")

session = requests.Session()
session.headers["User-Agent"] = USER_AGENT

# Fetch robots.txt ourselves so it uses our User-Agent. RobotFileParser.read() sends
# urllib's default UA, which Wikimedia rejects with a 403 -- and Python then treats
# a 403 as "everything is disallowed".
robots = RobotFileParser()
_robots_response = session.get(urljoin(BASE, "/robots.txt"), timeout=30)
_robots_response.raise_for_status()
robots.parse(_robots_response.text.splitlines())


def polite_get(url: str) -> requests.Response | None:
    """GET a URL if robots.txt allows it, then sleep. Returns None if disallowed/failed."""
    if not robots.can_fetch(USER_AGENT, url):
        print(f"  robots.txt disallows {url}, skipping")
        return None
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"  request failed for {url}: {error}")
        return None
    finally:
        time.sleep(DELAY_SECONDS)
    return response


def find_file_pages(category: str, limit: int) -> list[str]:
    """Step 2: parse a category page and return links to individual image pages."""
    url = f"{BASE}/wiki/Category:{category.replace(' ', '_')}"
    response = polite_get(url)
    if response is None:
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    # Only image thumbnails have a.mw-file-description (audio/video items don't).
    for anchor in soup.select("#mw-category-media li.gallerybox a.mw-file-description"):
        href = unquote(anchor.get("href", ""))
        if href.lower().endswith(IMAGE_EXTENSIONS):
            links.append(urljoin(BASE, anchor["href"]))
    return links[: limit * 2]  # a few spares in case some downloads fail


def find_image_url(file_page_url: str) -> str | None:
    """Step 3a: on an image's page, find the direct link to the image file."""
    response = polite_get(file_page_url)
    if response is None:
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    # ".fullImageLink img" is a screen-sized version, much smaller than the original.
    preview = soup.select_one(".fullImageLink img")
    if preview and preview.get("src"):
        return urljoin(BASE, preview["src"])
    original = soup.select_one(".fullMedia a")
    return urljoin(BASE, original["href"]) if original else None


def download(image_url: str, destination: Path) -> bool:
    """Step 3b: download the image bytes to disk."""
    response = polite_get(image_url)
    if response is None:
        return False
    destination.write_bytes(response.content)
    return True


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    total = 0
    with open(OUTPUT_DIR / "manifest.csv", "w", newline="", encoding="utf-8") as manifest:
        writer = csv.writer(manifest)
        writer.writerow(["breed", "filename", "source_page"])  # source page has license/author info

        for breed, category in BREEDS.items():
            print(f"[{breed}] crawling category '{category}'")
            breed_dir = OUTPUT_DIR / breed
            breed_dir.mkdir(exist_ok=True)
            saved = 0

            for file_page in find_file_pages(category, IMAGES_PER_BREED):
                if saved >= IMAGES_PER_BREED:
                    break
                image_url = find_image_url(file_page)
                if image_url is None:
                    continue
                extension = Path(urlparse(image_url).path).suffix.lower() or ".jpg"
                filename = f"{breed}_{saved + 1:02d}{extension}"
                if download(image_url, breed_dir / filename):
                    saved += 1
                    total += 1
                    writer.writerow([breed, f"{breed}/{filename}", file_page])
                    print(f"  saved {filename}")

            if saved < IMAGES_PER_BREED:
                print(f"  only got {saved}/{IMAGES_PER_BREED} for {breed}")

    print(f"\nDone: {total} images in {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
