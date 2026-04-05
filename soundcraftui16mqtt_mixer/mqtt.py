from soundcraftui16mqtt_mqtt import MqttClient

from loguru import logger
from os import path


class MixerMqttSender(MqttClient):
    def __init__(
        self, run_forever: bool = False, host: str = "localhost",
        port: int = 1883
    ) -> None:
        super().__init__(run_forever, host, port)
        self.update_topic = "config"

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        logger.debug("Mixer Mqtt Client connected")

    def _on_message(self, client, userdata, msg) -> None:
        logger.warning("Mixer Mqtt Client is just a sender")

    def publish(self, topic: str, msg: str) -> None:
        self.client.publish(
            path.join(self.update_topic, topic),
            self._message_encode(
                msg
            )
        )
