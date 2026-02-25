import pandas as pd
from ingestion.boeFetch import FetchAllMaturities as FetchUK
from ingestion.fredFetch import FetchAllMaturities as FetchUS
from storage.database import UpsertYields

def RunPipeline(startDate, endDate, conn):
    us = FetchUS(startDate, endDate)
    uk = FetchUK(startDate, endDate)

    combined = pd.concat([us, uk])

    UpsertYields(combined, conn)