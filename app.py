from pathlib import Path

from flask import Flask, render_template, request

from services.analyzer import analyze_ad
from services.catalog import load_microcategories

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
CATALOG_PATH = BASE_DIR / "data" / "rnc_mic_key_phrases.csv"
MICROCATEGORIES = load_microcategories(CATALOG_PATH)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        description = request.form.get("description", "").strip()
        source_mc_id = request.form.get("source_mc_id", type=int)
        result = analyze_ad(description, MICROCATEGORIES, source_mc_id=source_mc_id)
        return render_template("result.html", result=result)

    return render_template("index.html", microcategories=MICROCATEGORIES)


if __name__ == "__main__":
    app.run(debug=True)
