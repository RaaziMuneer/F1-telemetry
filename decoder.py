import struct

class F125Decoder:
    # Header format: uint16, 5*uint8, uint64, float, uint32, uint32, 2*uint8
    # Total: 29 bytes
    HEADER_FORMAT = '<HBBBBBQfIIBB'

    def unpack_header(self, data):
        """Unpacks the first 29 bytes to identify the packet."""
        header_data = data[:struct.calcsize(self.HEADER_FORMAT)]
        unpacked = struct.unpack(self.HEADER_FORMAT, header_data)
        
        return {
            "packetId": unpacked[5],        # Tells us if it's Telemetry, Lap Data, etc.
            "playerCarIndex": unpacked[10], # Your car's position in the data arrays
            "sessionTime": unpacked[7]      # Current timestamp of the session
        }

    def decode_telemetry(self, data, player_index):
        """Decodes Packet ID 6 (Car Telemetry) for the player car only."""
        # The telemetry packet contains an array of 22 cars. 
        # We jump the header (29) + (car_index * size_of_one_car_block)
        # Size of one car block in F1 25 is 60 bytes.
        car_block_size = 60
        offset = 29 + (player_index * car_block_size)
        
        # We'll extract: Speed (H), Throttle (f), Steer (f), Brake (f), Clutch (B), Gear (b), RPM (H)
        car_data = data[offset : offset + 15]
        speed, throttle, steer, brake, clutch, gear, rpm = struct.unpack('<HfffBbH', car_data)
        
        return {
            "speed": speed,
            "throttle": round(throttle * 100), # %
            "brake": round(brake * 100),       # %
            "gear": gear,
            "rpm": rpm
        }