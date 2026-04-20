import re
import pandas as pd
from os import path

def latency_analyze(target:str,log_text:str,folder_path:str = None)->float:
    # Extract latency values
    latencies = []
    time = []
    pattern = re.compile(
    rf"\[(.*?)\]\s*{target} average clicking latency:(.*?)\s*ms",
    re.IGNORECASE
    )
 
    for line in log_text.splitlines():
        print(line)
        match = pattern.search(line)
        if match:
            time.append(match.group(1))
            latencies.append(float(match.group(2))) 

    if not len(latencies):
        return None 
    # Create a DataFrame
    df = pd.DataFrame(latencies, columns=["Latency (ms)"])

    # Save the row data if path is provided
    if folder_path: 
        file_path = path.join(folder_path, "latency_test.txt") 
        with open(file_path, "w", encoding="utf-8") as f:
            i = 1
            f.write(f"Latency Target: {target}\n")
            for t, latency in zip(time, latencies):
                f.write(f"{str(i)} {t} {latency}\n")
                i = i+1
 
    # Show summary stats
    #print(f"target:{target}")
    #print("Min:", df["Latency (ms)"].min())
    #print("Max:", df["Latency (ms)"].max())
    #print("Average:", df["Latency (ms)"].mean())
    #print("StdDev:", df["Latency (ms)"].std())

    return df["Latency (ms)"].mean()

if __name__  == "__main__":
    message = " [2025-12-01 13:39:28.040729] mouse average clicking latency:156.986 ms" 
    print(latency_analyze('mouse',message,r'report\Report_20251224_152031'))

