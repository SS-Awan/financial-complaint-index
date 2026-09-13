import argparse
from pathlib import Path

import requests

CFPB_DOWNLOAD_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESTINATION = PROJECT_ROOT / "data" / "raw" / "complaints.csv.zip"


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()

        total_bytes = int(response.headers.get("content-length", 0))
        downloaded_bytes = 0

        with destination.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
                    downloaded_bytes += len(chunk)

                    if total_bytes:
                        percent = downloaded_bytes / total_bytes * 100
                        print(
                            f"\rDownloaded: {percent:.1f}%",
                            end="",
                            flush=True,
                        )

    print(f"\nSaved CFPB data to: {destination}")


parser = argparse.ArgumentParser()
parser.add_argument("--download", action="store_true")
args = parser.parse_args()

if args.download:
    download_file(CFPB_DOWNLOAD_URL, DEFAULT_DESTINATION)
else:
    print("Ready. Add --download when you want to start the full download.")
    