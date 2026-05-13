import sqlite3
import pandas as pd
import os

def export_telemetry_to_csv(db_name="f1_telemetry.db", output_folder="exports"):
    # 1. Connect to the database
    if not os.path.exists(db_name):
        print(f"Error: {db_name} not found. Drive some laps first!")
        return

    conn = sqlite3.connect(db_name)
    
    try:
        # 2. Load the data into a Pandas DataFrame
        # We sort by Session UID and then Frame ID to keep the lap sequence logical
        query = "SELECT * FROM telemetry ORDER BY session_uid, frame_id"
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("No data found in the database to export.")
            return

        # 3. Create export folder if it doesn't exist
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # 4. Generate a filename with a timestamp
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{output_folder}/f1_data_{timestamp}.csv"

        # 5. Export to CSV
        df.to_csv(csv_filename, index=False)
        print(f"✅ Success! Data exported to: {csv_filename}")
        print(f"📊 Total Rows Exported: {len(df)}")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    export_telemetry_to_csv()