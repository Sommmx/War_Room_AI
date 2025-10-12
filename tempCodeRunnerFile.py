import pandas as pd
import glob
import os



thresholds = {
    'cpu_pct': 85,
    'latency_ms': {
        'frontend': 350,
        'api': 350,
        'database': 200
    },
    'error_count_per_min': 0
}





correlation_window = 300


metrics_df = pd.read_csv('data/metrics.csv',sep = '\t',header=None, names = ['time_stamp','service','metric_name', 'value'])
metrics_df['time_stamp'] = pd.to_datetime(metrics_df['time_stamp'], format= '%d-%m-%Y %H:%M')
metrics_df = metrics_df.sort_values(by='time_stamp', ascending=True)







def metric_anamoly(df, thresholds):
    anamolies = []
    for _, row in df.iterrows():
        metric = row['metric_name']
        value = row['value']
        service = row['service']
        if metric in thresholds:
            threshold = thresholds[metric]
            if isinstance(threshold,dict):
                threshold_value = threshold.get(service, None)
            else:
                threshold_value = threshold
            if threshold_value is not None and value > threshold_value:
                anamolies.append(row)
    return pd.DataFrame(anamolies)




log_files = glob.glob("data/*.log")
logs = []

for file in log_files:
    df = pd.read_csv(file,sep="|", names=['timestamp', 'level', 'message'])
    df['timestamp'] = pd.to_datetime(df['timestamp'].str.strip(), format='%H:%M:%S', errors='coerce')
    df['service'] = os.path.basename(file).replace('.log','')
    logs.append(df)

logs_df = pd.concat(logs, ignore_index=True)

log_anomalies = logs_df[logs_df['level'].str.contains('ERROR', case=False, na=False)]
print(log_anomalies)
print("------------------------------------------------------------------------")
print(metric_anamoly(metrics_df,thresholds))
metric_anamolies = metric_anamoly(metrics_df,thresholds)



correlated = []

for _,m_row in metric_anamolies.iterrows():
    for _, l_row in log_anomalies.iterrows():
        time_diff = abs((m_row['time_stamp'] - l_row['timestamp']).total_seconds())
        if time_diff < correlation_window:
            correlated.append({
                'timestamp':m_row['time_stamp'],
                'metric_serrvice':m_row['service'],
                'metric_name': m_row['metric_name'],
                'metric_value':m_row['value'],
                'log_service':l_row['service'],
                'log_message':l_row['message']
                })
            
correlated_df = pd.DataFrame(correlated)

print(correlated)
