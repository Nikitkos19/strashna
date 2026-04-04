import csv
from pathlib import Path


def load_microcategories(csv_path):
    microcategories = []

    with Path(csv_path).open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            key_phrases = [
                phrase.strip()
                for phrase in row["keyPhrases"].split(";")
                if phrase.strip()
            ]
            microcategories.append(
                {
                    "mcId": int(row["mcId"]),
                    "mcTitle": row["mcTitle"].strip(),
                    "description": row.get("description", "").strip(),
                    "keyPhrases": key_phrases,
                }
            )

    return microcategories
