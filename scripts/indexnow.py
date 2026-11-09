#!/usr/bin/env python3
"""Submit every sitemap URL to IndexNow after a successful Pages deploy.

The key file must already be live at keyLocation. Exits non-zero unless IndexNow
returns 200 or 202.
"""
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = (ROOT / "indexnow.txt").read_text(encoding="utf-8").strip()
HOST = os.environ.get("INDEXNOW_HOST", "hastitore.github.io")
ORIGIN = os.environ.get("SITE_ORIGIN", "https://hastitore.github.io").rstrip("/")
BASE = os.environ.get("BASE_PATH", "/Kodulaen").rstrip("/")
SITE = ORIGIN + BASE
KEY_URL = f"{SITE}/{KEY}.txt"
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_urls():
    path = ROOT / "dist" / "sitemap.xml"
    tree = ET.parse(path)
    return [node.text.strip() for node in tree.findall(".//s:loc", NS) if node.text]


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "KodulaenIndexNow/0.1", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.read().decode("utf-8", "replace")


def wait_until_key_is_live():
    for _ in range(18):
        try:
            status, body = fetch(KEY_URL)
            if status == 200 and KEY in body:
                print(f"key live {status} {KEY_URL}")
                return
            print(f"key not ready {status}")
        except Exception as error:
            print(f"key check: {type(error).__name__}: {error}")
        time.sleep(10)
    sys.exit(f"IndexNow key file was not live at {KEY_URL}")


def submit(urls):
    payload = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_URL,
        "urlList": urls,
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "KodulaenIndexNow/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, response.read().decode("utf-8", "replace")[:500]
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")[:500]


def main():
    urls = sitemap_urls()
    if not urls:
        sys.exit("sitemap has no URLs")
    print(f"submitting {len(urls)} URLs")
    wait_until_key_is_live()
    status = None
    body = ""
    for attempt in range(4):
        status, body = submit(urls)
        print(f"attempt {attempt + 1}: {status} {body}")
        if status in (200, 202):
            return
        time.sleep(15)
    sys.exit(f"IndexNow failed with HTTP {status}: {body}")


if __name__ == "__main__":
    main()
