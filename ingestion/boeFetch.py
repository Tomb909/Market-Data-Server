import pandas as pd
import requests
from io import StringIO

# where key is the maturity expressed numerically in years
BOE_SERIES_CODES = {
    "IUDSNPY": 5.0,
    "IUDMNPY": 10.0,
    "IUDLNPY": 20.0,
}

def FetchAllMaturities(startDate, endDate) -> pd.DataFrame:
    start = pd.to_datetime(startDate)
    end   = pd.to_datetime(endDate) 
    seriesCodes = ",".join(BOE_SERIES_CODES.keys())

    url = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"
    params = {
        "csv.x": "yes",
        "Datefrom": start.strftime("%d/%b/%Y"),
        "Dateto": end.strftime("%d/%b/%Y"),
        "SeriesCodes": seriesCodes, 
        "UsingCodes": "Y",
        "CSVF": "TN",
    }
    headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.bankofengland.co.uk/boeapps/database/",
    }

    res = requests.get(url, params=params, headers=headers)
    res.raise_for_status()

    df_raw = pd.read_csv(StringIO(res.text))
    print(df_raw[df_raw.isnull().any(axis=1)].head(10))
    print(df_raw.isnull().sum())

    # so each row is one date/maturity observation, rather than having series codes as columns make them values under a series code field
    df = df_raw.melt(id_vars=["DATE"], var_name="series_code", value_name="yield")

    df["maturity"] = df["series_code"].map(CodeToMaturity)

    # normalise
    df["date"] = pd.to_datetime(df["DATE"], dayfirst=True)
    df["country"] = "UK"
    df["instrument"] = "Gilt"
    df["yield"] = pd.to_numeric(df["yield"], errors="coerce") / 100

    # remove missing values
    df = df.dropna(subset=["yield", "maturity"])

    return df[["date", "country", "instrument", "maturity", "yield"]]

def CodeToMaturity(code: str) -> float:
    return BOE_SERIES_CODES[code]

if __name__ == "__main__":
    result = FetchAllMaturities("2023-01-01", "2025-01-01")
    print(result[:500])