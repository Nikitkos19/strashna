from pathlib import Path
import json
import re

from flask import Flask, render_template, request

from services.analyzer import analyze_ad, build_public_response
from services.catalog import load_microcategories
from services.request_parser import parse_request_json
from services.split_model import train_should_split_predictor

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "data" / "rnc_mic_key_phrases.csv"
DATASET_PATH = BASE_DIR / "data" / "rnc_dataset" / "rnc_dataset.csv"
MICROCATEGORIES = load_microcategories(CATALOG_PATH)
SHOULD_SPLIT_PREDICTOR = train_should_split_predictor(DATASET_PATH)


def format_response_json(public_response):
    response_json = json.dumps(public_response, ensure_ascii=False, indent=2)
    detected_mc_ids = public_response.get("detectedMcIds", [])
    compact_detected_mc_ids = json.dumps(detected_mc_ids, ensure_ascii=False)

    return re.sub(
        r'"detectedMcIds": \[[\s\S]*?\]',
        f'"detectedMcIds": {compact_detected_mc_ids}',
        response_json,
        count=1,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_payload = request.form.get("payload", "").strip()
        parsed_request = parse_request_json(raw_payload)
        description = parsed_request["description"]
        source_mc_id = parsed_request["mcId"]

        result = analyze_ad(
            description,
            MICROCATEGORIES,
            source_mc_id=source_mc_id,
            should_split_predictor=SHOULD_SPLIT_PREDICTOR,
        )
        public_response = build_public_response(result)
        response_json = format_response_json(public_response)
        return render_template("result.html", response_json=response_json)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
