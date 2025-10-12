import pandas as pd
from .config import correlation_window

def correlate(metric_anomalies, log_anomalies):
    correlated = []
    for _, m_row in metric_anomalies.iterrows():
        for _, l_row in log_anomalies.iterrows():
            time_diff = abs((m_row['time_stamp'] - l_row['timestamp']).total_seconds())
            if time_diff < correlation_window:
                correlated.append({
                    'timestamp': m_row['time_stamp'],
                    'metric_service': m_row['service'],
                    'metric_name': m_row['metric_name'],
                    'metric_value': m_row['value'],
                    'log_service': l_row['service'],
                    'log_message': l_row['message']
                })
    return pd.DataFrame(correlated)