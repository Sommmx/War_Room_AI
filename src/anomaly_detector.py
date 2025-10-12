import pandas as pd
from .config import thresholds



def metric_anomaly(df: pd.DataFrame):
    anomalies = []
    for _, row in df.iterrows():
        metric = row['metric_name']
        value = row['value']
        service = row['service']

        if metric in thresholds:
            threshold = thresholds[metric]
            if isinstance(threshold, dict):
                threshold_value = threshold.get(service)
            else:
                threshold_value = threshold
            if threshold_value is not None and value > threshold_value:
                anomalies.append(row)
    return pd.DataFrame(anomalies)