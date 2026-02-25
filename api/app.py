from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from curve.interpolation import GetLatestInterpolatedYield, GetTimeSeriesInterpolatedYield
from storage.database import GetConnection

app = Flask(__name__)

@app.route("/")
def home():
    return "Market Data Server is running"

# endpoint to get latest interpolated yield for a given country and maturity
@app.route("/latest", methods=["GET"])
def getLatest():
    country = request.args.get("country", type=str)
    maturity = request.args.get("maturity", type=str)

    required = ["country", "maturity"]
    missing = [param for param in required if request.args.get(param) is None]


    if missing:
        return jsonify({"error": f"Missing required query parameters: {', '.join(missing)}"}), 400
    
    conn = GetConnection()
    try:
        res = GetLatestInterpolatedYield(country, float(maturity), conn)
    except ValueError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()

    return jsonify(res)

# endpoint to get time series of interpolated yields for a given country and maturity, between a given start and end date
# default start date is 1 year ago and default end date is today
@app.route("/timeseries", methods=["GET"])
def getTimeSeries():
    country = request.args.get("country", type=str)
    maturity = request.args.get("maturity", type=str)
    start = request.args.get("start_date", default=(datetime.today() - timedelta(days=365)).strftime("%Y-%m-%d"), type=str)
    end = request.args.get("end_date", default=datetime.today().strftime("%Y-%m-%d"), type=str)

    required = ["country", "maturity", "start_date", "end_date"]
    missing = [param for param in required if request.args.get(param) is None]

    if missing:
        return jsonify({"error": f"Missing required query parameters: {', '.join(missing)}"}), 400
    
    conn = GetConnection()
    try:
        res = GetTimeSeriesInterpolatedYield(country, float(maturity), start, end, conn)
    except ValueError as e:
        conn.close()
        return jsonify({"error": str(e)}), 400
    conn.close()

    return jsonify(res)

if __name__ == "__main__":
    app.run(debug=True)