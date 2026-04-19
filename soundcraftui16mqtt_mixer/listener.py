from .main import MixerBase
from .mqtt import MixerMqttSender

from threading import Thread
from loguru import logger


class MixerListener(MixerBase):
    def __init__(
        self, mixer_ip: str, mixer_port: int, mqtt_host: str = "localhost",
        mqtt_port: int = 1883
    ) -> None:
        super().__init__(mixer_ip, mixer_port)
        self.recv_thread = Thread(
            target=self._recv_thread,
            args=()
        )
        self.mqtt_client = MixerMqttSender(host=mqtt_host, port=mqtt_port)

    def start(self) -> None:
        self.mqtt_client.start()
        self.connect()
        if self.connected:
            logger.debug("Listener to Soundcraft ui16 connected")
            self.mqtt_client.send_endpoint(self.ip, self.port)
            self.mqtt_client.send_status(True)
        else:
            self.logger.critical("Soundcraft Listener could not connect")
            raise RuntimeError("Soundcraft Listener could not connect")

    def stop(self) -> None:
        self.mqtt_client.stop()
        self.terminate()

    def _recv_thread(self) -> None:
        buffer = ""
        while not self.exit.is_set():
            # save new data to buffer
            buffer += self.client.recv(2048).decode()
            if "\n" not in buffer:
                # If no message delimiter is found wait for new messages
                continue
            # split buffer on delimiter into parts
            parts = buffer.split("\n")
            # Save everything except last unfinished element
            data = parts[0:len(parts)-1]
            # set unfinished back in buffer
            buffer = parts[len(parts)-1]
            for message in data:
                if "SETD" in message:
                    # Send message using mqtt
                    self._send_message(message)
                elif message.startswith("VU"):
                    logger.info("Possible VU Meter message! {message}")
                else:
                    logger.debug("SKIP LISTENER MESSAGE: {message}")
        self.mqtt_client.send_status(False)

    def _send_message(self, message) -> None:
        logger.debug(message)
        _, body, value = message.split('^')
        body_list = body.split('.')
        if body_list[0] == "var":
            self.mqtt_client.publish(
                "var",
                {
                    "var": body_list[1],
                    "value": value
                }
            )
        elif body_list[0] == "afs":
            self.mqtt_client.publish(
                "afs",
                {
                    "option": body_list[1],
                    "value": value
                }
            )
        elif body_list[0] == "m":
            self.mqtt_client.publish(
                "master",
                {
                    "channel": body_list[1],
                    "value": value
                }
            )
        elif len(body_list) == 3:
            self.mqtt_client.publish(
                body_list[0],
                {
                    "channel": body_list[1],
                    "function": body_list[2],
                    "value": value
                }
            )
        elif len(body_list) == 4:
            self.mqtt_client.publish(
                body_list[0],
                {
                    "channel": body_list[1],
                    "option": body_list[2],
                    "function": body_list[3],
                    "value": value
                }
            )
        elif len(body_list) == 5:
            self.mqtt_client.publish(
                body_list[0],
                {
                    "channel": body_list[1],
                    "option": body_list[2],
                    "option_channel": body_list[3],
                    "function": body_list[4],
                    "value": value
                }
            )
        else:
            self.mqtt_client.publish("error", message)
