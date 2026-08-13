import asyncio
import socket
import time

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Digits, Footer, Header, Label, Log

from core.database import AsyncTelemetryLogger
from core.packets import F125Decoder


class F1TelemetryTUI(App):
    CSS = """
    Screen { 
        layout: grid; 
        grid-size: 2 3; 
    }
    .status-box {
        column-span: 2;
        border: solid yellow;
        padding: 1;
        content-align: center middle;
        text-style: bold;
    }
    .metric-box { 
        border: solid green; 
        padding: 1; 
        margin: 1; 
        height: 100%; 
    }
    Log { 
        column-span: 2; 
        border: solid blue; 
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        # Status Label displaying connection state
        yield Label("🔴 GAME NOT RUNNING (Waiting for Telemetry...)", id="game_status", classes="status-box")
        yield Vertical(Label("SPEED (KM/H)"), Digits("000", id="speed"), classes="metric-box")
        yield Vertical(Label("GEAR / RPM"), Digits("N - 00000", id="gear_rpm"), classes="metric-box")
        yield Log(id="console_log")
        yield Footer()

    def on_mount(self) -> None:
        self.logger = AsyncTelemetryLogger()
        self.decoder = F125Decoder()
        self.last_packet_time = 0  # Timestamp of last received packet
        self.game_active = False

        # Start listening for UDP packets and watching game status
        asyncio.create_task(self.udp_listener())
        asyncio.create_task(self.connection_watchdog())

    async def connection_watchdog(self):
        """Checks every second if packets have stopped arriving."""
        status_label = self.query_one("#game_status", Label)
        
        while True:
            current_time = time.time()
            # If no packet received in the last 3 seconds
            if current_time - self.last_packet_time > 3.0:
                if self.game_active or self.last_packet_time == 0:
                    self.game_active = False
                    status_label.update("🔴 GAME NOT RUNNING / PAUSED")
                    status_label.styles.border = ("solid", "red")
            else:
                if not self.game_active:
                    self.game_active = True
                    status_label.update("🟢 GAME RUNNING")
                    status_label.styles.border = ("solid", "green")
            
            await asyncio.sleep(1)

    async def udp_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", 20777))
        sock.setblocking(False)

        log = self.query_one("#console_log", Log)
        log.write_line("🏎️ F1 25 Telemetry Listener Active on Port 20777...")

        loop = asyncio.get_running_loop()
        car_state = {}

        while True:
            try:
                data, _ = await loop.sock_recvfrom(sock, 2048)
                self.last_packet_time = time.time()  # Reset watchdog timer

                header = self.decoder.unpack_header(data)

                if header:
                    pid = header['packet_id']
                    idx = header['player_car_index']

                    if pid == 6:  # Telemetry Packet
                        telemetry = self.decoder.decode_car_telemetry(data, idx)
                        if telemetry:
                            car_state.update(telemetry)
                            self.query_one("#speed", Digits).update(f"{telemetry['speed']:03d}")
                            self.query_one("#gear_rpm", Digits).update(f"{telemetry['gear']} - {telemetry['rpm']}")

                    elif pid == 7:  # Car Status (ERS) Packet
                        status = self.decoder.decode_car_status(data, idx)
                        if status:
                            car_state.update(status)

                    # Log aggregated state asynchronously
                    if 'speed' in car_state:
                        self.logger.queue_frame(header['session_uid'], header['frame_id'], car_state)

            except Exception:
                await asyncio.sleep(0.001)

if __name__ == "__main__":
    app = F1TelemetryTUI()
    app.run()