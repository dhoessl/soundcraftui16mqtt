from .main import MixerBase

from loguru import logger


class MixerSender(MixerBase):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)

    def start(self) -> None:
        self.connect()
        if self.connected:
            logger.debug("Soundcraft Ui16 Sender connected")
        else:
            logger.error("Soundcraft Ui16 could not connect")

    def stop(self) -> None:
        self.terminate()

    def send_packet(self, command: str) -> bool:
        if not self.connected:
            logger.warning("Soundcraft Ui16 not connected")
            return False
        self.client.send(command.encode("UTF-8"))
        return True

    def send_setd(self, body: str, value: str | float) -> bool:
        if not self.connected:
            logger.warning("Soundcraft Ui16 not connected")
            return False
        self.client.send(
            f"SETD^{body}^{value}\n".encode("UTF-8")
        )
        return True

    def master(self, value: str | float) -> bool:
        return self.send_setd("m.mix", value)

    def record(self) -> bool:
        return self.send_packet("RECTOGGLE\n")

    def tempo(self, value: str | int) -> bool:
        for channel in range(1, 4):
            if not self.send_setd(f"f.{channel}.bpm", value):
                return False
        return True

    def mix(self, kind: str, channel: str | int, value: str | float) -> bool:
        return self.send_setd(f"{kind}.{channel}.mix", value)

    def mute(self, kind: str, channel: str | int, value: str | float) -> bool:
        return self.send_setd(f"{kind}.{channel}.mute", value)

    def fx(
        self, kind: str, channel: str | int, fx: str | int, value: str | float
    ) -> bool:
        return self.send_setd(f"{kind}.{channel}.fx.{fx}.value", value)

    def fx_mute(
        self, kind: str, channel: str | int, fx: str | int, value: str | int
    ) -> bool:
        return self.send_setd(f"{kind}.{channel}.fx.{fx}.mute", value)

    def fx_setting(
        self, fx: str | int, par: str | int, value: str | float
    ) -> bool:
        return self.send_setd(f"f.{fx}.par{par}", value)

    def easy_eq(
        self, kind: str, channel: str | int, index: str | int,
        value: str | float
    ) -> bool:
        return self.send_setd(f"{kind}.{channel}.eq.b{index}.gain", value)
