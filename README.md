# Web Crawling for Dog Pictures

A small, polite web crawler that downloads dog images from Wikimedia Commons, to learn how crawlers work.

## Setup and usage

Requires Python 3.10+.

```bash
pip install requests beautifulsoup4
python crawler.py
```

Images are saved to `dog_images/<breed>/`, and `dog_images/manifest.csv` records
the source page for each one. The crawler pauses 1.5 seconds between requests
and makes roughly 300 of them, so a full run takes around 8 minutes.

## Breeds

The crawler downloads 10 images for each of these 10 breeds (100 in total):

| Breed | Commons category |
| --- | --- |
| Labrador Retriever | `Labrador Retriever` |
| Golden Retriever | `Golden Retriever` |
| German Shepherd | `German Shepherd Dog` |
| Beagle | `Beagle (dog)` |
| Bulldog | `Bulldog` |
| Poodle | `Poodles` |
| Dachshund | `Dachshund` |
| Siberian Husky | `Siberian Husky` |
| Pug | `Pug` |
| Chihuahua | `Chihuahua (dog)` |

To change the breeds or how many images to fetch, edit `BREEDS` and
`IMAGES_PER_BREED` at the top of `crawler.py`. Commons category names are
inconsistent (`Pug` but `Poodles`), so check a category exists in a browser
before adding it. Categories can also contain off-topic files, so skim the results.

## How it works

The classic crawler loop:

1. Start from a seed URL (a Commons category page for a breed).
2. Fetch the HTML and parse it for links (each image's `File:` page).
3. Visit each file page, find the actual image URL, and download it.
4. Repeat for every breed until we have enough images.

## Politeness rules

- Obey `robots.txt`.
- Identify ourselves with a User-Agent.
- Pause between requests.

## Licensing

Images on Wikimedia Commons each carry their own license (Creative Commons,
public domain, and others), and many require attribution. The `source_page`
column in `manifest.csv` links to each image's Commons page, which shows its
license and author. Check it before reusing an image beyond personal learning.
The `dog_images/` folder is git-ignored, so the images are not committed to this repo.
