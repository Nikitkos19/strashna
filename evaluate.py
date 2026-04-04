import ast
import csv
from collections import Counter
from pathlib import Path

from services.analyzer import analyze_ad
from services.catalog import load_microcategories

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "data" / "rnc_mic_key_phrases.csv"
DATASET_PATH = BASE_DIR / "data" / "rnc_dataset" / "rnc_dataset.csv"


def parse_int_list(raw_value):
    value = raw_value.strip()
    if not value:
        return []
    return list(ast.literal_eval(value))


def parse_bool(raw_value):
    return raw_value.strip().lower() == "true"


def safe_divide(numerator, denominator):
    if denominator == 0:
        return 0.0
    return numerator / denominator


def main():
    microcategories = load_microcategories(CATALOG_PATH)
    false_positives = Counter()
    false_negatives = Counter()
    split_mismatches = Counter()

    tp = 0
    fp = 0
    fn = 0
    split_correct = 0
    total = 0

    with DATASET_PATH.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            total += 1
            target_detected = set(parse_int_list(row["targetDetectedMcIds"]))
            source_mc_id = int(row["sourceMcId"])
            expected_should_split = parse_bool(row["shouldSplit"])

            result = analyze_ad(row["description"], microcategories, source_mc_id=source_mc_id)
            predicted_detected = set(result["detectedMcIds"])

            tp += len(predicted_detected & target_detected)
            fp += len(predicted_detected - target_detected)
            fn += len(target_detected - predicted_detected)

            for mc_id in predicted_detected - target_detected:
                false_positives[mc_id] += 1
            for mc_id in target_detected - predicted_detected:
                false_negatives[mc_id] += 1

            if result["shouldSplit"] == expected_should_split:
                split_correct += 1
            else:
                case_key = f"{row['caseType']}::{row['sourceMcId']}"
                split_mismatches[case_key] += 1

    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    split_accuracy = safe_divide(split_correct, total)

    print(f"Total rows: {total}")
    print(f"Detected precision: {precision:.4f}")
    print(f"Detected recall: {recall:.4f}")
    print(f"Detected F1: {f1:.4f}")
    print(f"shouldSplit accuracy: {split_accuracy:.4f}")
    print()
    print("Top false positives:", false_positives.most_common(10))
    print("Top false negatives:", false_negatives.most_common(10))
    print("Top split mismatches:", split_mismatches.most_common(10))


if __name__ == "__main__":
    main()
