import pandas as pd
import glob
import os
from config import BASE_DATE




def load_metrics(filepath: str):
    df = pd.read_csv(filepath, sep='\t', header=None, names=['time_stamp', 'service', 'metric_name', 'value'])
    df['time_stamp'] = pd.to_datetime(df['time_stamp'], format='%d-%m-%Y %H:%M', errors='coerce')
    return df.sort_values(by='time_stamp')


def load_logs(folder_path: str):
    log_files = glob.glob(f"{folder_path}/*.log")
    logs = []
    base_date = pd.to_datetime(BASE_DATE)
    for file in log_files:
        df = pd.read_csv(file, sep="|", names=['timestamp', 'level', 'message'])
        df['timestamp'] = pd.to_datetime(df['timestamp'].str.strip(), format='%H:%M:%S', errors='coerce')
        df['timestamp'] = df['timestamp'].apply(
            lambda t: base_date + pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
            if pd.notnull(t) else pd.NaT
        )
        df['service'] = os.path.basename(file).replace('.log', '')
        logs.append(df)
    return pd.concat(logs, ignore_index=True)