#!/usr/bin/env python3

import requests
import csv
import time
from collections import defaultdict

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc=None, **kwargs):
        # No progress bar without the real tqdm, but at 304 sequential API
        # calls (network latency + a 0.25s throttle sleep each) this can take
        # several minutes, so print something rather than going silent.
        items = list(iterable)
        total = len(items)
        prefix = f"{desc}: " if desc else ""
        for i, item in enumerate(items, start=1):
            print(f"\r{prefix}{i}/{total}", end="", flush=True)
            yield item
        print()


API_URL = "https://api.pota.app/park/activations/"

INPUT_FILE = "nl_parks.txt"
OUTPUT_FILE = "leaderboard.csv"

TOP_N = 25

# Always included in the CSV, even when ranked below TOP_N, so you can see
# your own standing without having to search a much longer full dump.
MY_CALLSIGN = "PD3AN"

HEADERS = {
    "User-Agent": "POTA-NL-Leaderboard-Analyzer/1.0"
}


def load_parks(filename):
    """
    Load POTA park references from file.
    """
    parks = []

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            park = line.strip().upper()

            if park and park.startswith("NL-"):
                parks.append(park)

    return parks


def get_park_activations(park):
    """
    Query POTA API for activation history.
    """

    url = API_URL + park

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:
        print(f"Error retrieving {park}: {e}")
        return []


def extract_activators(data):
    """
    Extract valid POTA activator callsigns from API response.

    A POTA activation requires at least 10 QSOs.
    """

    calls = set()

    if not isinstance(data, list):
        return calls

    for item in data:

        if not isinstance(item, dict):
            continue

        # Only count qualifying activations
        if item.get("totalQSOs", 0) < 10:
            continue

        callsign = item.get("activeCallsign")

        if callsign:
            calls.add(callsign.upper())

    return calls



def build_leaderboard(parks):

    """
    Returns:
        callsign -> set of parks activated
    """

    activator_parks = defaultdict(set)


    for park in tqdm(parks, desc="Processing parks"):

        data = get_park_activations(park)

        activators = extract_activators(data)


        for call in activators:
            activator_parks[call].add(park)


        # avoid hammering API
        time.sleep(0.25)


    return activator_parks



def save_results(activator_parks):

    ranking = []

    for call, parks in activator_parks.items():

        ranking.append(
            (
                call,
                len(parks)
            )
        )


    ranking.sort(
        key=lambda x: x[1],
        reverse=True
    )

    # Full 1-indexed rank for every activator, computed before truncating to
    # TOP_N, so MY_CALLSIGN's real position is known even if it's far outside
    # the top of the list.
    ranked = [
        (rank, call, count)
        for rank, (call, count) in enumerate(ranking, start=1)
    ]

    top_rows = ranked[:TOP_N]
    my_row = next(
        (row for row in ranked if row[1] == MY_CALLSIGN),
        None
    )

    rows = list(top_rows)

    if my_row and my_row not in top_rows:
        rows.append(my_row)
    elif not my_row:
        print(f"Note: {MY_CALLSIGN} has no qualifying activations yet, skipping from output.")

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow(
            [
                "Rank",
                "Callsign",
                "NL Parks Activated"
            ]
        )


        for rank, call, count in rows:

            writer.writerow(
                [
                    rank,
                    call,
                    count
                ]
            )


    print()
    print("Top activators:")
    print("----------------")

    for rank, call, count in top_rows:

        print(
            f"{rank:2d}. {call:12s} {count} parks"
        )

    if my_row and my_row not in top_rows:
        print("----------------")
        rank, call, count = my_row
        print(
            f"{rank:2d}. {call:12s} {count} parks  (your rank)"
        )



def main():

    parks = load_parks(INPUT_FILE)

    print(
        f"Loaded {len(parks)} NL parks"
    )


    activator_parks = build_leaderboard(
        parks
    )


    save_results(
        activator_parks
    )


if __name__ == "__main__":
    main()
