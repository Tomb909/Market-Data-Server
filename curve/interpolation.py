from nelson_siegel_svensson.calibrate import calibrate_ns_ols
import numpy as np
import matplotlib.pyplot as plt

# fits a nelson siegel curve to the given maturities and yields, and returns a callable curve object that can be evaluated at any maturity
def FitCurve(maturities, yields):
    curve, status = calibrate_ns_ols(np.array(maturities), np.array(yields))
    if not status.success:
        raise RuntimeError(f"Nelson-Siegel fit failed: {status.message}")
    return curve

# fetches maturities and yields for the given date and country from the database, fits a curve to then return the interpolated yield for the given maturity 
def GetInterpolatedYieldForDate(date, country, maturity, conn) -> float:
    # np arrays of maturities and yields for a given date and country
    maturities, yields = GetMaturitiesAndYields(date, country, conn)

    curve = FitCurve(maturities, yields)

    # evaluate curve to get yield at given maturity
    return curve(maturity)

# Gets the interpolated yield for a specified maturity and country from the data for the latest date in the DB
def GetLatestInterpolatedYield(country, maturity, conn) -> dict:
    latest_date = GetLatestDate(country, conn)

    interpolated_yield = GetInterpolatedYieldForDate(latest_date, country, maturity, conn)

    return {
        "date": latest_date,
        "country": country,
        "maturity": maturity,
        "yield": interpolated_yield
    }

# Gets the interpolated yields for a given maturity between a start date and end date
def GetTimeSeriesInterpolatedYield(country, maturity, startDate, endDate, conn) -> list[dict]:
    cursor = conn.cursor()

    # get all dates for which we have data for the given country and date range
    cursor.execute(
        "SELECT DISTINCT date FROM yields WHERE country = ? AND date BETWEEN ? AND ? ORDER BY date",
        (country, startDate, endDate)
    )
    rows = cursor.fetchall()
    if not rows:
        raise ValueError(f"No data found for {country} between {startDate} and {endDate}")
    
    output = []
    data = []
    for row in rows:
        date = row["date"]
        interpolated_yield = GetInterpolatedYieldForDate(date, country, maturity, conn)
        data.append({
            "date": date,
            "yield": interpolated_yield
        })
    
    output.append({
        "country": country,
        "maturity": maturity,
        "data": data
    })
    
    return output

# gets the yields and maturities for the latest data in the db, fits a ns curve
# and returns the original yields and maturities as well as the points of the 
# interpolated curve between maturities of 1 day to 50 years
def GetLatestCurveData(country, conn) -> dict:
    latestDate = GetLatestDate(country, conn)

    # np arrays of maturities and yields for a given date and country
    maturities, yields = GetMaturitiesAndYields(latestDate, country, conn)

    curve = FitCurve(maturities, yields)

    x = np.linspace(1/365, 50, 300)
    fitted = curve(x)

    return {
        "date": latestDate,
        "country": country,
        "points": list(zip(maturities.tolist(), yields.tolist())),
        "curve": list(zip(x.tolist(), fitted.tolist()))}

# gets all maturities and yields for a given date and country
def GetMaturitiesAndYields(date, country, conn):
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
    
    return np.array(maturities), np.array(yields)

# Gets the latest date for which we have data in the DB for a particular country
def GetLatestDate(country, conn):
    cursor = conn.cursor()

    # get latest date for which we have data for the given country and date range
    cursor.execute(
        "SELECT date FROM yields WHERE country = ? ORDER BY date DESC LIMIT 1",
        (country,)
    )
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"No data found for {country}")
    
    return row["date"]
