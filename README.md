# Market-Data-Server
This project pulls US Treasury data from Federal Reserve Economic Data (FRED) and UK gilt data from Bank of England, stores it in a local SQLite database, and exposes it via a Flask API and Streamlit frontend.

It supports:
* Historical time series queries for specific maturities
* Yield curve construction at a point in time
* Interpolation/extrapolation across maturities using the Nelson-Siegel-Svensson model

## Running
1. In the main directory create a .env file with a FRED api key in the format `FRED_API_KEY="examplekey"`
2. Run `pip install -r requirements.txt`
3. Run `python -m storage.database` - this initialises the db
4. Run `python -m scripts.ingest --start <start-date> --end <end-date>` - this populates the db with data
5. Then you can:
    * `python -m api.app` - Run the API
    * `python -m streamlit run frontend/webApp.py` - Run the web app


## Data Sources
* For querying Bank of England Gilt Data I used: https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp
    - I used their [documentation](https://www.bankofengland.co.uk/boeapps/database/help.asp?Back=Y&Highlight=CSV#CSV) to customise the parameters in the query. I also had to programmatically set the header of the request to look like a browser to avoid an invalid client error.
    - BOE gives nominal par yield gilt data at only 3 maturities of 5 year, 10 year and 20 year which is much sparser than FRED, I found series codes for these maturities by searching [here](https://www.bankofengland.co.uk/boeapps/database)
* For US Treasury data I used: https://api.stlouisfed.org/fred/series/observations
    - I similarly used the FRED's [documentation](https://fred.stlouisfed.org/docs/api/fred/series_observations.html) to figure out how to query the above endpoint and I created an account to get an API key which is stored in a .env file
    - From this API I was able to get constant maturity Treasury yields with maturities: 1M, 3M, 6M, 1Y, 2Y, 5Y, 7Y, 10Y, 20Y, 30Y.


## Design and Implementation Choices

### Data Ingestion
* Series codes for the data are mapped to their maturity in dictionaries within the Fetch files, this is an unavoidable bit of hard coding because the program needs to have the different series codes somehow in order to query for the data
* I chose to use the FRED API because CSV download URLs are less stable and not always designed as programmatic interfaces
* As previously mentioned I could only find 3 maturities for nominal par yield on the BOE website which makes curve normalisation not as accurate compared to the FRED data

### Storage
* I set up a SQLite database with a single yields table which is appropriate for a service needing to work locally such as this one
* The yields table has a composite primary key of `(date, country, maturity)` which ensures one yield per date/country/maturity. This combined with using `INSERT OR REPLACE` makes the running of ingestion to be idempotent as rows will never be duplicated, simply overwriting existing rows if they already exist
* In `UpsertYields`, `executemany` and named place holders are used to bulk insert and bind values to the SQL. This is more efficient than row-by-row inserts and safe against SQL injection.
* SQLite doesn't have a DATE type so I store the dates as string in a format of `YYYY-MM-DD`
* Connections to the DB are created by the caller and passed into all functions. This avoids unnecessary reconnection and gives control over the scope of DB communication. The API uses try/finally blocks to guarantee closure of the connection.

### Curve Normalisation
* I used Nelson-Siegel-Svensson for interpolation because after looking into it alongside polynomial functions I saw that both seem to be widely used for yield curves but central banks tend to use the Nelson-Siegel-Svenson model.
* To implement NSS curve normalisation I use an aptly named `nelson_siegel_svensson` python library which fits a curve based on maturities and yields which can then be evaluated at any maturity which allows for interpolation and extrapolation across a 1 day to 50 year grid.

### API
* Using flask and sqlite for a balance of working with a db (albeit local) for extensibility and suitability for a small app
* data types and various properties of parameters are validated, such as maturity needing to be positive, start date needing to be before end date
* 404 no content errors are returned if there is no data in the DB for the specified parameters
* 400 errors if parameters are missing and the missing parameters are returned so the caller knows what was wrong with the request

### Frontend
* I implemented a time series chart where you can select country, maturity, start date and end date, this shows the graphs that you can produce with the raw data I obtained from FRED and BOE when using a standard maturity but when using maturities between the original values it will interpolate the yields
* There is then a yield curve snapshot graph which shows the relationship between yield and maturity at partciular point in time (in this instance it is the most recent day with data in the DB). You can select Country which lets you see the difference between US treasuries and UK Gilts.
    - This graph requires querying the /latest end point for every maturity on the x axis we want to plot a yield which is costly compared to a single request from a new endpoint which would be doable with more time

## What Could be Improved With More Time
* Originally I connected the frontend to the backend/interpolation file without the API and just queried the data to create a yield curve snapshot for the most recent data but then decided that in a production environment you would be querying the API endpoints for the data but to make a yield curve snapshot with the specified endpoints you would have to query /latest for every maturity value you were plotting so with more time I'd implement an endpoint that takes in a list of maturities, a country and a date and gives the interpolated yield for each maturity so plot the graph with one GET request
* Cleanup the front end and make it look more appealing
* Set up automatic tests for api endpoints and internal methods thoroughly with happy paths, edge and corner cases
* Look for some additional sources for UK nominal par yield gilt data to get more maturities for more accurate interpolation
* I'd add some fallback curve normalisation for if nelson-siegel fails to fit
* I could add another layer of data normalisation at pipeline.py with assertions and ensure consistent standard/schema
* Create a bash or python script to reduce the number of commands needed to be ran by the user to set up the server and I would test that it works on a fresh install

## Testing/Demo
- Valid Examples
    * `curl "http://127.0.0.1:5000/timeseries?country=US&maturity=10&start_date=2024-01-01&end_date=2024-12-31"`
    * `curl "http://127.0.0.1:5000/latest?country=US&maturity=2.5"`
- Invalid Examples 
    * `curl "http://127.0.0.1:5000/latest?country=US&maturity=-20.5"`
    * `curl "http://127.0.0.1:5000/latest?country=France&maturity=2.5"`
    * `curl "http://127.0.0.1:5000/latest?maturity=2.5"`
    * `curl "http://127.0.0.1:5000/timeseries?country=US&maturity=10&start_date=2024-01-01&end_date=2023-12-31"`

## Resources
- https://nelson-siegel-svensson.readthedocs.io/_/downloads/en/latest/pdf/
- https://www.geeksforgeeks.org/python/command-line-arguments-in-python/
- https://docs.python.org/3/library/sqlite3.html
- https://www.tutorialspoint.com/python_sqlite/python_sqlite_quick_guide.htm
- https://pandas.pydata.org/docs/reference/general_functions.html
- https://www.bankofengland.co.uk/boeapps/database/help.asp?Back=Y&Highlight=CSV#CSV
- https://fred.stlouisfed.org
- https://flask.palletsprojects.com/en/stable/quickstart/
- https://www.practicaldatascience.org/notebooks/class_5/week_1/2.2.2_making_plots_pretty_2.html
- https://www.dmo.gov.uk/responsibilities/gilt-market/about-gilts/
