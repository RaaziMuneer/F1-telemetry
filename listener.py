import socket
import struct

# --- Phase 2: The Decoder Class ---
class F125Decoder:
    HEADER_FORMAT = '<HBBBBBQfIIBB'

    def unpack_header(self, data):
        # We need at least 29 bytes for the header
        if len(data) < 29:
            return None
        header_data = data[:29]
        unpacked = struct.unpack(self.HEADER_FORMAT, header_data)
        return {
            "packetId": unpacked[5],
            "playerCarIndex": unpacked[10]
        }

    def decode_telemetry(self, data, player_index):
        # Jump to the specific car's data block
        car_block_size = 60
        offset = 29 + (player_index * car_block_size)
        
        # Pulling Speed, Throttle, Brake, Gear, RPM
        car_data = data[offset : offset + 15]
        speed, throttle, steer, brake, clutch, gear, rpm = struct.unpack('<HfffBbH', car_data)
        
        return {
            "speed": speed,
            "throttle": round(throttle * 100),
            "brake": round(brake * 100),
            "gear": gear,
            "rpm": rpm
        }

# --- Phase 1: The Socket Setup (DEFINING 'sock' HERE) ---
UDP_IP = "0.0.0.0"
UDP_PORT = 20777

# Create and bind the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

decoder = F125Decoder()

print(f"🚀 Project Started. Listening on port {UDP_PORT}...")

# --- Combined Loop ---
try:
    while True:
        # Now 'sock' is defined in the same scope as the loop
        data, addr = sock.recvfrom(2048)
        
        header = decoder.unpack_header(data)
        
        if header and header['packetId'] == 6:  # 6 is the Telemetry Packet
            stats = decoder.decode_telemetry(data, header['playerCarIndex'])
            
            # This will print the data on one line that updates constantly
            output = f"SPEED: {stats['speed']} km/h | GEAR: {stats['gear']} | RPM: {stats['rpm']} | THR: {stats['throttle']}%"
            print(output, end='\r')

except KeyboardInterrupt:
    print("\nStopping Project...")
finally:
    sock.close()