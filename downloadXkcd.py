# Downloads every single XKCD comic

# Importing Python standard libraries
import requests
import os
import bs4
from urllib.parse import urljoin, urlparse
import argparse

# Global constants
BASE_URL = "https://xkcd.com/"
DEFAULT_OUT_DIR = "xkcd"
TIMEOUT = 20
CHUNK_SIZE = 100000


def fix_img_url(img_src, page_url):
    """
    (str, str) -> str
    Convert protocol-relative URLs (//imgs...) and relative URLs into absolute URLs.
    """
    if img_src.startswith("//"):
        return "https:" + img_src
    return urljoin(page_url, img_src)


def filename_from_url(url):
    """
    Extract a safe filename from a URL
    """
    return os.path.basename(urlparse(url).path)


def save_file(url, out_path):
    """
    Download a URL to out_path
    """
    # Skips if file already exists
    if os.path.exists(out_path):
        return

    res = requests.get(url, stream=True, timeout=TIMEOUT)
    res.raise_for_status()

    with open(out_path, "wb") as image_file:
        for chunk in res.iter_content(CHUNK_SIZE):
            if chunk:
                image_file.write(chunk)


def parse_args():
    parser = argparse.ArgumentParser(description="Download XKCD comics automatically")
    parser.add_argument(
        "--out-dir",
        default=DEFAULT_OUT_DIR,
        help=f"Directory to save comics (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of comics to download (default: download all)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    out_dir = args.out_dir
    limit = args.limit
    count = 0

    # Starting URL
    page_url = BASE_URL

    # Store comics in ./xkcd
    os.makedirs(out_dir, exist_ok=True)

    while True:
        # Stop early if we've reached the user-specified limit
        if limit is not None and count >= limit:
            break

        # 1) Download the page.
        print(f"Downloading page {page_url}...")
        res = requests.get(page_url, timeout=TIMEOUT)
        res.raise_for_status()

        soup = bs4.BeautifulSoup(res.text, "html.parser")

        # 2) Find the URL of the comic image.
        comic_imgs = soup.select("#comic img")

        if not comic_imgs:
            print("Could not find comic image.")

        else:
            img_src = comic_imgs[0].get("src", "")
            if img_src:
                img_url = fix_img_url(img_src, page_url)
                out_file = os.path.join(out_dir, filename_from_url(img_url))

                print(f"Downloading image {img_url}...")
                save_file(img_url, out_file)

                count += 1

            else:
                print("Found #comic img but src was empty.")

        # 3) Get the Prev button's url.
        prev_link = soup.select('a[rel = "prev"]')
        if not prev_link:
            print("No prev link found; stopping.")
            break

        prev_href = prev_link[0].get("href", "").strip()
        if prev_href == "#":
            break

        elif not prev_href:
            print("Prev link had no href; stopping.")
            break

        page_url = urljoin(page_url, prev_href)

    print("Done.")


if __name__ == "__main__":
    main()