import csv
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline


class ShouldSplitPredictor:
    def __init__(self, pipeline, threshold=0.6):
        self.pipeline = pipeline
        self.threshold = threshold

    def predict(self, description):
        probability = self.predict_proba(description)
        return probability >= self.threshold

    def predict_proba(self, description):
        return float(self.pipeline.predict_proba([description])[0][1])


def train_should_split_predictor(dataset_path):
    descriptions = []
    labels = []

    with Path(dataset_path).open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        for row in reader:
            descriptions.append(row["description"])
            labels.append(row["shouldSplit"].strip().lower() == "true")

    pipeline = Pipeline(
        [
            (
                "features",
                FeatureUnion(
                    [
                        (
                            "word_tfidf",
                            TfidfVectorizer(
                                lowercase=True,
                                ngram_range=(1, 2),
                                min_df=2,
                                max_features=25000,
                            ),
                        ),
                        (
                            "char_tfidf",
                            TfidfVectorizer(
                                lowercase=True,
                                analyzer="char_wb",
                                ngram_range=(3, 5),
                                min_df=2,
                                max_features=20000,
                            ),
                        ),
                    ]
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    pipeline.fit(descriptions, labels)
    return ShouldSplitPredictor(pipeline, threshold=0.6)
