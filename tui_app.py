import asyncio
import socket
from textual.app 
import App, ComposeResult
from textual.widgets 
import Header, Footer, Digits, Log, Label
from textual.containers 
import Horizontal, Vertical
from core.packets import F125Decoder
from core.database import AsyncTelemetryLogger

class F1TelemetryTUI(App):
    CSS = """
    Screen { layout: grid; grid-size: 2 2; }
    .metric-box { border: solid green; padding: 1; margin: 1; height: 100%; }
    Log { column-span: 2; border: solid blue; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Vertical(Label("SPEED (KM/H)"), Digits("000", id="speed"), classes="metric-box")
        yield Vertical(Label("GEAR / RPM"), Digits("N - 00000", id="gear_rpm"), classes="metric-box")
        yield Log(id="console_log")
        yield Footer()

    def on_mount(self) -> None:
        self.logger = AsyncTelemetryLogger()
        self.decoder = F125Decoder()
        asyncio.create_task(self.udp_listener())

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
                header = self.decoder.unpack_header(data)

                if header:
                    pid = header['packet_id']
                    idx = header['player_car_index']

                    if pid == 6:  # Telemetry
                        telemetry = self.decoder.decode_car_telemetry(data, idx)
                        if telemetry:
                            car_state.update(telemetry)
                            self.query_one("#speed", Digits).update(f"{telemetry['speed']:03d}")
                            self.query_one("#gear_rpm", Digits).update(f"{telemetry['gear']} - {telemetry['rpm']}")

                    elif pid == 7:  # Car Status (ERS)
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