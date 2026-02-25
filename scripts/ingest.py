import argparse
from datetime import datetime, timedelta
from storage.database import GetConnection
from ingestion.pipeline import RunPipeline

def ParseArgs():
    parser = argparse.ArgumentParser(description="Ingest market data into local DB")
    parser.add_argument("--end", type=str, default=datetime.today().strftime("%Y-%m-%d"), help="End date DD-MM-YYYY")
    parser.add_argument("--start", type=str, default=(datetime.today() - timedelta(days=730)).strftime("%Y-%m-%d"), help="Start date DD-MM-YYYY")
    return parser.parse_args()


if __name__ == "__main__":
    args = ParseArgs()

    print(f"Running pipeline from {args.start} to {args.end}")

    conn = GetConnection()
    RunPipeline(args.start, args.end, conn) 
    conn.close()

    print("Ingestion complete")