import streamlit as st
import pandas as pd
from curve.interpolation import GetLatestInterpolatedYield, GetTimeSeriesInterpolatedYield, GetLatestCurveData
from storage.database import GetConnection
import matplotlib.pyplot as plt
import numpy as np

def GetX(series):
    return [p[0] for p in series] 

def GetY(series):
    return [p[1] * 100 for p in series] 

colours = ["#2B2F42", "#8D99AE", "#EF233C", "#EDF2F4", "#F4A261"]

st.subheader("Current Yield Curve")

conn = GetConnection()
ukLatestCurve = GetLatestCurveData("UK", conn)
usLatestCurve = GetLatestCurveData("US", conn)
conn.close()

fig, ax = plt.subplots()
ax.plot(GetX(ukLatestCurve["curve"]), GetY(ukLatestCurve["curve"]), label="UK", color=colours[0])
ax.plot(GetX(usLatestCurve["curve"]), GetY(usLatestCurve["curve"]), label="US", color=colours[1])
ax.scatter(GetX(ukLatestCurve["points"]), GetY(ukLatestCurve["points"]), color=colours[2], label="UK Observed", marker='x')
ax.scatter(GetX(usLatestCurve["points"]), GetY(usLatestCurve["points"]), color=colours[4], label="US Observed", marker='x')

ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)

ax.yaxis.set_ticks_position("left")
ax.xaxis.set_ticks_position("bottom")
ax.spines["bottom"].set_bounds(min(GetX(ukLatestCurve["curve"])), max(GetX(ukLatestCurve["curve"])))

ax.set_xlabel("Maturity (years)")
ax.set_ylabel("Yield (%)")
ax.legend()

st.pyplot(fig)

