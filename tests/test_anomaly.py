import threading
from sim import vfd_sim
from client.modbus_client import ModbusClient
import numpy as np
from ai.anomaly import AnomalyDetector, extract_features


def make_transactions(count, latency, seed=42):
    rng = np.random.default_rng(seed)

    return [
        {
            "latency": max(0.1, rng.normal(latency, 0.5)),
            "reply_length": 11,
            "is_exception": False,
        }
        for _ in range(count)
    ]


def test_feature_extraction():
    transactions = make_transactions(20, 2.0)

    features = extract_features(transactions)

    assert features.shape == (2, 5)


def test_healthy_traffic_is_not_flagged_excessively():
    training = make_transactions(600, 2.0, seed=42)
    detector = AnomalyDetector().fit(training)

    healthy = make_transactions(200, 2.0, seed=100)
    predictions = detector.predict(healthy)

    anomaly_rate = np.mean(predictions == -1)

    assert anomaly_rate <= 0.15


def test_delayed_traffic_is_detected():
    training = make_transactions(600, 2.0, seed=42)
    detector = AnomalyDetector().fit(training)

    delayed = make_transactions(200, 32.0, seed=200)
    predictions = detector.predict(delayed)

    detection_rate = np.mean(predictions == -1)

    assert detection_rate >= 0.80


def test_real_simulator_detects_30ms_latency():
    original_latency = vfd_sim.LATENCY_MS

    server = vfd_sim.Server(
        ("127.0.0.1", 0),
        vfd_sim.Handler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )
    thread.start()

    port = server.server_address[1]

    try:
        # Collect 600 healthy transactions.
        vfd_sim.LATENCY_MS = 0

        client = ModbusClient(port=port)
        client.connect()

        for _ in range(600):
            client.read_holding_registers(0, 1)

        healthy = client.transaction_log.copy()
        client.close()

        # Train the detector on actual healthy simulator traffic.
        detector = AnomalyDetector().fit(healthy)

        # Introduce 30 ms simulator latency.
        vfd_sim.LATENCY_MS = 30

        client = ModbusClient(port=port)
        client.connect()

        for _ in range(200):
            client.read_holding_registers(0, 1)

        delayed = client.transaction_log.copy()
        client.close()

        predictions = detector.predict(delayed)
        detection_rate = np.mean(predictions == -1)

        print(f"\nAnomaly detection rate: {detection_rate:.1%}")

        assert detection_rate >= 0.80

    finally:
        vfd_sim.LATENCY_MS = original_latency
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
