from nelson_siegel_svensson.calibrate import calibrate_ns_ols
import numpy as np
import matplotlib.pyplot as plt

# fits a nelson siegel curve to the given maturities and yields, and returns a callable curve object that can be evaluated at any maturity
def FitCurve(maturities, yields):
    curve, status = calibrate_ns_ols(np.array(maturities), np.array(yields))
    if not status.success:
        raise RuntimeError(f"Nelson-Siegel fit failed: {status.message}")
    return curve

# fetches yields for the given date and country from the database, fits a curve to then return the interpolated yield for the given maturity 
def GetInterpolatedYield(date, country, maturity, conn) -> float:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT maturity, yield FROM yields WHERE date = ? AND country = ?",
        (date, country)
    )
    rows = cursor.fetchall()
    if not rows:
        raise ValueError(f"No data found for {country} on {date}")
    
    maturities, yields = [], []
    for row in rows:
        maturities.append(row["maturity"])
        yields.append(row["yield"])

    # np arrays of maturities and yields for a given date and country
    maturities, yields = np.array(maturities), np.array(yields)

    curve = FitCurve(maturities, yields)

    # evaluate curve at given maturity
    return curve(maturity)

