
import numpy as np
from sklearn.neighbors import LocalOutlierFactor


WINDOW_SIZE = 10


def extract_features(transactions, window_size=WINDOW_SIZE):
    """Convert transaction records into statistical feature windows."""
    features = []

    for start in range(0, len(transactions) - window_size + 1, window_size):
        window = transactions[start:start + window_size]

        latencies = np.array(
            [item["latency"] for item in window], dtype=float
        )
        reply_lengths = [
            item["reply_length"] for item in window
        ]
        exceptions = [
            item["is_exception"] for item in window
        ]

        features.append([
            np.mean(latencies),
            np.percentile(latencies, 95),
            np.std(latencies),
            np.mean(exceptions),
            np.mean(reply_lengths),
        ])

    return np.asarray(features, dtype=float)


class AnomalyDetector:
    def __init__(self):
        self.mean = None
        self.std = None
        self.model = LocalOutlierFactor(
            n_neighbors=20,
            novelty=True,
            contamination=0.02,
        )

    def fit(self, healthy_transactions):
        features = extract_features(healthy_transactions)

        if len(features) < 21:
            raise ValueError("Need at least 21 healthy windows")

        self.mean = features.mean(axis=0)
        self.std = features.std(axis=0)
        self.std[self.std == 0] = 1.0

        standardized = (features - self.mean) / self.std
        self.model.fit(standardized)

        return self

    def predict(self, transactions):
        if self.mean is None:
            raise RuntimeError("Detector has not been fitted")

        features = extract_features(transactions)

        if len(features) == 0:
            raise ValueError("Not enough transactions")

        standardized = (features - self.mean) / self.std

        # LOF returns -1 for anomalies and 1 for normal windows.
        return self.model.predict(standardized)
