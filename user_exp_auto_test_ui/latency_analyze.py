import re
import pandas as pd
import matplotlib.pyplot as plt


def latency_analyze(target:str,log_text:str)->float:
    # Extract latency values
    pattern = re.compile(rf"{target} average clicking latency:(.*?) ms")
    latencies = [float(x) for x in pattern.findall(log_text)]
    if not len(latencies):
        return None

    # Create a DataFrame
    df = pd.DataFrame(latencies, columns=["Latency (ms)"])
    # Show summary stats
    #print(f"target:{target}")
    #print("Min:", df["Latency (ms)"].min())
    #print("Max:", df["Latency (ms)"].max())
    #print("Average:", df["Latency (ms)"].mean())
    #print("StdDev:", df["Latency (ms)"].std())

    return df["Latency (ms)"].mean()

