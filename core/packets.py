import struct

class F125Decoder:
    HEADER_FORMAT = '<HBBBBBQfIIBB'  # 29 Bytes
    HEADER_SIZE = 29

    @staticmethod
    def unpack_header(data: bytes):
        if len(data) < F125Decoder.HEADER_SIZE:
            return None
        unpacked = struct.unpack(F125Decoder.HEADER_FORMAT, data[:29])
        return {
            "packet_format": unpacked[0],
            "packet_id": unpacked[5],
            "session_uid": unpacked[6],
            "frame_id": unpacked[8],
            "player_car_index": unpacked[10]
        }

    @staticmethod
    def decode_car_telemetry(data: bytes, player_index: int):
        """Packet ID 6: Car Telemetry (60 bytes per car)"""
        car_block_size = 60
        offset = F125Decoder.HEADER_SIZE + (player_index * car_block_size)
        
        # Extract 19 bytes: Speed(H), Throttle(f), Steer(f), Brake(f), Clutch(B), Gear(b), RPM(H)
        car_data = data[offset : offset + 19]
        if len(car_data) < 19:
            return None
            
        speed, throttle, steer, brake, clutch, gear, rpm = struct.unpack('<HfffbH', car_data)
        
        return {
            "speed": speed,
            "throttle": round(throttle * 100, 1),
            "steer": round(steer, 2),
            "brake": round(brake * 100, 1),
            "gear": gear,
            "rpm": rpm
        }

    @staticmethod
    def decode_car_status(data: bytes, player_index: int):
        """Packet ID 7: Car Status (Extracts ERS energy & mode)"""
        car_block_size = 55
        offset = F125Decoder.HEADER_SIZE + (player_index * car_block_size)
        car_data = data[offset : offset + car_block_size]
        
        if len(car_data) < car_block_size:
            return None
            
        # Extract ERS store energy (float) & ERS deploy mode (uint8)
        # Offset details according to F1 UDP spec
        ers_store_joules = struct.unpack_from('<f', car_data, 29)[0]
        ers_deploy_mode = struct.unpack_from('<B', car_data, 33)[0]
        
        return {
            "ers_store_joules": round(ers_store_joules, 1),
            "ers_deploy_mode": ers_deploy_mode
        }