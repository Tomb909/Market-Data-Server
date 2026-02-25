import os
import pandas as pd
from dotenv import load_dotenv
import requests

FRED_SERIES_IDS = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30"
}
load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

# return observations for a given series from fred API
def FetchSeries(seriesID, startDate, endDate) -> list[dict]:
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": seriesID,
        "observation_start": startDate,
        "observation_end": endDate,
        "api_key": API_KEY,
        "file_type": "json"
    }

    res = requests.get(url, params=params)
    res.raise_for_status()

    observations = res.json()["observations"]

    output = []
    for obs in observations:
        output.append({"date": obs["date"], "value": obs["value"]})
    return output


def FetchAllMaturities(startDate, endDate) -> pd.DataFrame:
    rows = []

    for label, seriesID in FRED_SERIES_IDS.items():

        observations = FetchSeries(seriesID, startDate, endDate)

        for obs in observations:
            rows.append({
                "date": obs["date"],
                "value": obs["value"],
                "label": label
            })
        
    df = pd.DataFrame(rows)

    # FRED marks missing values as "."
    df = df[df["value"] != "."]

    df["yield"] = df["value"].astype(float) / 100 # FRED returns eg/ 4.25, we want 0.0425

    # convert label to numeric maturity in years
    df["maturity"] = df["label"].map(LabelToYears)

    df["country"] = "US"
    df["instrument"] = "Treasury"

    return df[["date", "country", "instrument", "maturity", "yield"]]

def LabelToYears(label: str) -> float:
    if label.endswith("M"):
        return int(label[:-1]) / 12
    elif label.endswith("Y"):
        return float(label[:-1])

# if __name__ == "__main__":
#     result = FetchAllMaturities("2023-01-01", "2025-01-01")
#     print(result[:5])