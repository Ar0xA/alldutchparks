#!/usr/bin/env python3

import csv
import io

import requests

ALL_PARKS_URL = "https://pota.app/all_parks.csv"
OUTPUT_FILE = "nl_parks.txt"

HEADERS = {
    "User-Agent": "POTA-NL-Park-Fetcher/1.0"
}


def fetch_active_nl_parks():
    """
    Download the POTA all_parks.csv and return sorted active NL-xxxx references.
    """

    response = requests.get(ALL_PARKS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))

    parks = [
        row["reference"]
        for row in reader
        if row["reference"].startswith("NL-") and row["active"] == "1"
    ]

    parks.sort()

    return parks


def main():
    parks = fetch_active_nl_parks()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for park in parks:
            f.write(park + "\n")

    print(f"Saved {len(parks)} active NL parks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
