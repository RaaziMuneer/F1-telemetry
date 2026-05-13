import streamlit as st
import pandas as pd
import socket
import struct
import time

# --- REUSE YOUR DECODER CLASS FROM PHASE 2 ---
class F125Decoder:
    HEADER_FORMAT = '<HBBBBBQfIIBB'
    def unpack_header(self, data):
        if len(data) < 29: return None
        unpacked = struct.unpack(self.HEADER_FORMAT, data[:29])
        return {"packetId": unpacked[5], "playerCarIndex": unpacked[10]}

    def decode_telemetry(self, data, player_index):
        offset = 29 + (player_index * 60)
        car_data = data[offset : offset + 15]
        speed, throttle, steer, brake, clutch, gear, rpm = struct.unpack('<HfffBbH', car_data)
        return {"speed": speed, "throttle": throttle * 100, "brake": brake * 100, "gear": gear}

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="F1 25 Live Telemetry", layout="wide")
st.title("🏎️ F1 25 Real-Time Analysis")

# Create placeholders for live numbers
col1, col2, col3 = st.columns(3)
speed_gauge = col1.empty()
gear_gauge = col2.empty()
throttle_bar = col3.empty()

# Create a chart for Throttle vs Brake
chart_placeholder = st.empty()
history = pd.DataFrame(columns=["Throttle", "Brake"])

# --- UDP INITIALIZATION ---
UDP_IP = "127.0.0.1"
UDP_PORT = 20777
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(False) # Don't freeze the UI if no data is coming
decoder = F125Decoder()

# --- MAIN UI LOOP ---
while True:
    try:
        data, addr = sock.recvfrom(2048)
        header = decoder.unpack_header(data)

        if header and header['packetId'] == 6:
            stats = decoder.decode_telemetry(data, header['playerCarIndex'])

            # 1. Update Metrics
            speed_gauge.metric("Speed (km/h)", stats['speed'])
            gear_gauge.metric("Current Gear", stats['gear'])
            
            # 2. Update Live Graphing
            new_data = pd.DataFrame({"Throttle": [stats['throttle']], "Brake": [stats['brake']]})
            history = pd.concat([history, new_data], ignore_index=True).tail(50) # Keep last 50 frames
            chart_placeholder.line_chart(history)

    except BlockingIOError:
        # No data received yet, just wait
        time.sleep(0.01)
    except Exception as e:
        st.error(f"Error: {e}")
        break