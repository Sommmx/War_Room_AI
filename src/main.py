# src/main.py

from data_loader import load_metrics, load_logs
from anomaly_detector import metric_anomaly
from correlator import correlate
from root_cause import analyze_root_cause
import os

def main():
    DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
    metrics = load_metrics(os.path.join(DATA_DIR, "metrics.csv"))
    logs = load_logs(DATA_DIR)
    log_anomalies = logs[logs['level'].str.contains('ERROR', case=False, na=False)]
    metric_anomalies = metric_anomaly(metrics)
    print(metric_anomalies)
    print("--------------------------------------------------------")
    print(log_anomalies)
    correlated = correlate(metric_anomalies, log_anomalies)
    analyze_root_cause(correlated)

if __name__ == "__main__":
    main()
