import requests
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import date, timedelta

API_URL = "http://127.0.0.1:5000"

def GetTimeSeries(country, maturity, startDate, endDate):
    params = {
        "country": country,
        "maturity": maturity,
        "start_date": startDate,
        "end_date": endDate
    }
    res = requests.get(f"{API_URL}/timeseries", params=params)
    
    if res.status_code != 200:
        st.error(f"Error fetching time series: {res.text}")
        return None

    return res.json()

def GetLatestYield(country, maturity):
    params = {
        "country": country,
        "maturity": maturity
    }
    res = requests.get(f"{API_URL}/latest", params=params)
    
    if res.status_code != 200:
        st.error(f"Error fetching latest yields: {res.text}")
        return None

    return res.json()

def GetLatestYields(country, maturityStart, maturityEnd):
    yields = []
    for maturity in np.arange(maturityStart, maturityEnd + 0.1, 0.5):
        params = {
            "country": country,
            "maturity": maturity
        }
        res = requests.get(f"{API_URL}/latest", params=params)
        
        if res.status_code == 200:
            yields.append(res.json())
        else:
            st.warning(f"Error fetching yield for maturity {maturity}: {res.text}")
    
    return yields

def main():
    colours = ["#2B2F42", "#8D99AE", "#EF233C", "#EDF2F4", "#F4A261"]
    st.subheader("Time Series Chart")

    country = st.selectbox("Country", ["UK", "US"])
    maturity = st.number_input("Maturity (years)", min_value=0.0, step=0.1, value=10.0, max_value=50.0)

    startDate = st.date_input("Start Date", value=date.today() - timedelta(days=365))
    endDate = st.date_input("End Date", value=date.today())

    if startDate >= endDate:
        st.error("Start date must be before end date.")
    else:
        timeSeries = GetTimeSeries(country, maturity, startDate.strftime("%Y-%m-%d"), endDate.strftime("%Y-%m-%d"))
        if timeSeries:
            data = timeSeries[0]["data"]
            dates = [d["date"] for d in data]
            yields = [d["yield"] * 100 for d in data]
            
            fig, ax = plt.subplots(figsize=(12, 4))
            ax.plot(dates, yields, label=f"{country} {maturity}Y", color=colours[0])
            ax.grid(axis="y", alpha=0.3)

            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.spines["top"].set_visible(False)
            n = len(dates)
            ax.set_xticks([dates[i] for i in range(0, n, n // 6)])

            ax.yaxis.set_ticks_position("left")
            ax.xaxis.set_ticks_position("bottom")

            ax.set_xlabel("Date")
            ax.set_ylabel("Yield (%)")
            ax.legend()

            st.pyplot(fig)
    
    st.subheader("Latest Yield Curve Snapshot")

    country = st.selectbox("Country", ["UK", "US"], key="latestCountry")

    latestYields = GetLatestYields(country, 1/365, 50) # get yields for maturities between 1 day and 50 years
    if latestYields:
        x = np.arange(1/365, 50 + 0.1, 0.5) 
        y = [y["yield"] * 100 for y in latestYields]
        fig, ax = plt.subplots(figsize=(12, 4))
        ax.title.set_text(f"{country} Yield Curve Snapshot ({latestYields[0]['date']})")
        ax.plot(x, y, label=f"{country} Yield Curve", color=colours[2])
        ax.grid(axis="y", alpha=0.3)

        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["top"].set_visible(False)
        n = len(x)
        ax.set_xticks([x[i] for i in range(0, n, n // 10)])

        ax.yaxis.set_ticks_position("left")
        ax.xaxis.set_ticks_position("bottom")

        ax.set_xlabel("Maturity (years)")
        ax.set_ylabel("Yield (%)")
        ax.legend()

        st.pyplot(fig)

if __name__ == "__main__":
    main()

