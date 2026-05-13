import streamlit as st
import pandas as pd
import google.generativeai as genai
import socket
import struct
import time
import sqlite3
from decoder import F125Decoder 
from logger import TelemetryLogger

# --- 1. AI COACH FUNCTION ---
def get_ai_coaching(lap_df):
    try:
        # Use your actual API Key here
        genai.configure(api_key="YOUR_GEMINI_API_KEY")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        max_speed = lap_df['speed'].max()
        avg_throttle = lap_df['throttle'].mean()
        
        prompt = f"""
        You are a professional F1 Race Engineer. Analyze this lap data:
        - Max Speed: {max_speed} km/h
        - Average Throttle: {avg_throttle:.1f}%
        
        Provide 2 high-level technical tips for improvement focusing on car balance.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Engineer is busy: {e}"

# --- 2. STREAMLIT UI SETUP ---
st.set_page_config(page_title="F1 25 Live Telemetry", layout="wide")
st.title("🏎️ F1 25 Real-Time Analysis")

# Sidebar Buttons (Placed OUTSIDE the loop for stability)
st.sidebar.header("🕹️ Controls")
if st.sidebar.button("Get AI Coaching"):
    try:
        conn = sqlite3.connect("f1_telemetry.db")
        # Pulling a snapshot of recent data
        last_lap = pd.read_sql_query("SELECT * FROM telemetry ORDER BY rowid DESC LIMIT 2000", conn)
        conn.close()
        
        with st.spinner('Analyzing your driving...'):
            advice = get_ai_coaching(last_lap)
            st.sidebar.markdown("### 🎧 Race Engineer Advice")
            st.sidebar.info(advice)
    except Exception as e:
        st.sidebar.error(f"Could not load data for AI: {e}")

if st.sidebar.button("Export Database to CSV"):
    try:
        conn = sqlite3.connect("f1_telemetry.db")
        df = pd.read_sql_query("SELECT * FROM telemetry", conn)
        conn.close()
        csv = df.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Download CSV", data=csv, file_name='f1_telemetry.csv', mime='text/csv')
    except Exception as e:
        st.sidebar.error(f"Export failed: {e}")

# Ghost Comparison Upload
st.sidebar.header("👻 Ghost Comparison")
uploaded_file = st.sidebar.file_uploader("Upload Rival CSV", type="csv")
ghost_data = None
if uploaded_file:
    ghost_data = pd.read_csv(uploaded_file)
    st.sidebar.success("Ghost Data Loaded!")

# Live UI Placeholders
col1, col2, col3 = st.columns(3)
speed_gauge = col1.empty()
gear_gauge = col2.empty()
rpm_gauge = col3.empty()
chart_placeholder = st.empty()

# --- 3. UDP INITIALIZATION ---
UDP_IP = "127.0.0.1"
UDP_PORT = 20777
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(False)
except OSError:
    st.error(f"Port {UDP_PORT} is busy. Close other scripts and refresh.")
    st.stop()

decoder = F125Decoder()
db_logger = TelemetryLogger()
frame_count = 0
history = pd.DataFrame(columns=["Live_Speed", "Live_Throttle"])

# --- 4. MAIN TELEMETRY LOOP ---
while True:
    try:
        data, addr = sock.recvfrom(2048)
        header = decoder.unpack_header(data)

        if header and header['packetId'] == 6:
            try:
                stats = decoder.decode_telemetry(data, header['playerCarIndex'])
                if stats:
                    # Logging
                    db_logger.log_data(header['sessionUID'], header['frameId'], stats)
                    frame_count += 1
                    if frame_count % 100 == 0:
                        db_logger.save()

                    # UI Updates
                    speed_gauge.metric("Speed (km/h)", stats['speed'])
                    gear_gauge.metric("Gear", stats['gear'])
                    rpm_gauge.metric("RPM", stats['rpm'])

                    # Data for Charting
                    new_row = pd.DataFrame([{"Live_Speed": stats['speed'], "Live_Throttle": stats['throttle']}])
                    history = pd.concat([history, new_row], ignore_index=True).tail(100)

                    # Prepare Plotting DataFrame
                    plot_df = history.copy().reset_index(drop=True)

                    # Ghost Logic Sync
                    if ghost_data is not None:
                        current_ghost_idx = frame_count % len(ghost_data)
                        ghost_slice = ghost_data.iloc[current_ghost_idx : current_ghost_idx + len(plot_df)]
                        if len(ghost_slice) == len(plot_df):
                            plot_df["Ghost_Speed"] = ghost_slice["speed"].values
                    
                    chart_placeholder.line_chart(plot_df)

            except struct.error:
                pass # Skip malformed packets

    except BlockingIOError:
        time.sleep(0.01) # Wait for next UDP packet
    except Exception as e:
        st.write(f"Loop Error: {e}")
        break