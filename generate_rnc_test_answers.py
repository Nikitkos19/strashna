import csv
import json
from pathlib import Path

from services.analyzer import analyze_ad, build_public_response
from services.catalog import load_microcategories
from services.split_model import train_should_split_predictor

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "data" / "rnc_test.csv"
OUTPUT_PATH = BASE_DIR / "data" / "rnc_test_with_answers.csv"
CATALOG_PATH = BASE_DIR / "data" / "rnc_mic_key_phrases.csv"
DATASET_PATH = BASE_DIR / "data" / "rnc_dataset" / "rnc_dataset.csv"


def main():
    microcategories = load_microcategories(CATALOG_PATH)
    should_split_predictor = train_should_split_predictor(DATASET_PATH)
    rows = []

    with INPUT_PATH.open(encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)

        for row in reader:
            request_payload = json.loads(row["request"])
            result = analyze_ad(
                request_payload["description"],
                microcategories,
                source_mc_id=int(request_payload["mcId"]),
                should_split_predictor=should_split_predictor,
            )
            response_payload = build_public_response(result)
            rows.append(
                {
                    "request": json.dumps(request_payload, ensure_ascii=False),
                    "response": json.dumps(response_payload, ensure_ascii=False),
                }
            )

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["request", "response"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
