import struct

class F125Decoder:
    # Header format: uint16, 5*uint8, uint64, float, uint32, uint32, 2*uint8
    # Total: 29 bytes
    HEADER_FORMAT = '<HBBBBBQfIIBB'

    def unpack_header(self, data):
        """Unpacks the first 29 bytes to identify the packet."""
        if len(data) < 29:
            return None
        header_data = data[:29]
        unpacked = struct.unpack(self.HEADER_FORMAT, header_data)
        
        return {
            "packetId": unpacked[5],        # Tells us if it's Telemetry, Lap Data, etc.
            "playerCarIndex": unpacked[10], # Your car's position in the data arrays
            "sessionUID": unpacked[6],      # Needed for Phase 4 database logging
            "frameId": unpacked[8]          # Needed for Phase 4 database logging
        }

    def decode_telemetry(self, data, player_index):
        """Decodes Packet ID 6 (Car Telemetry) for the player car only."""
        car_block_size = 60
        offset = 29 + (player_index * car_block_size)
        
        # FIX: We extract 18 bytes to perfectly match the 18-byte structure template
        car_data = data[offset : offset + 18]
        
        # Safety Check: If data slice is incomplete, reject it cleanly
        if len(car_data) < 18:
            return None
            
        speed, throttle, steer, brake, clutch, gear, rpm = struct.unpack('<HfffBbH', car_data)
        
        return {
            "speed": speed,
            "throttle": round(throttle * 100), # %
            "brake": round(brake * 100),       # %
            "gear": gear,
            "rpm": rpm
        }