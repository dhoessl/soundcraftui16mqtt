#!/usr/bin/env python3

from loguru import logger
from os import path

from soundcraftui16mqtt_mqtt import MqttClient


class DatabaseMqttListener(MqttClient):
    def __init__(
            self, run_forever: bool = False, host: str = "localhost",
            port: int = 1883
    ) -> None:
        super().__init__(run_forever, host, port)
        self.request_topic = "database_request"
        self.update_topic = "database_update"

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        self.client.subscribe(f"{self.update_topic}/all/#")
        logger.debug(f"Listener Client connected to {self.update_topic}/all/#")
        self.client.subscribe(f"{self.update_topic}/{self.id}/#")
        logger.debug(
            f"Listener Client connected to {self.update_topic}/{self.id}/#"
        )

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        decoded_msg = self._message_decoder(msg.payload.decode())
        if topic.startswith(self.update_topic):
            if path.split(topic)[1] == "channel":
                self.channel_update(decoded_msg)
            elif path.split(topic)[1] == "channel_fx":
                self.chjannel_fx_update(decoded_msg)
            elif path.split(topic)[1] == "fx":
                self.fx_update(decoded_msg)
            elif path.split(topic)[1] == "master":
                self.master_update(decoded_msg)
            elif path.split(topic)[1] == "bpm":
                self.bpm_update(decoded_msg)
            else:
                logger.debug(
                    f"Unsolved: {topic} => {decoded_msg}"
                )
            return None
        logger.debug(f"Unsolved: {topic} => {decoded_msg}")

    def channel_update(self, msg: dict) -> None:
        logger.warning("Please set a channel_update(msg) function")
        return None

    def channel_fx_update(self, msg: dict) -> None:
        logger.warning("Please set a channel_fx_update(msg) function")
        return None

    def fx_update(self, msg: dict) -> None:
        logger.warning("Please set a fx_update(topic, msg) function")
        return None

    def master_update(self, msg: str) -> None:
        logger.warning("Please set a master_update(msg) function")
        return None

    def bpm_update(self, msg: str) -> None:
        logger.warning("Please set a bpm_update(msg) function")
        return None

    def req_channel_update(self, param: str, channel: int | str) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "channel"),
            {
                "channel": str(channel),
                "param": param
            }
        )

    def req_channel_fx_update(
        self, param: str, fx_id: int | str, channel: int | str
    ) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "channel_fx"),
            {
                "channel": str(channel),
                "fx": str(fx_id),
                "param": param
            }
        )

    def req_fx_update(self, param: str, fx_id: int | str) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "fx"),
            {
                "fx": str(fx_id),
                "param": param
            }
        )

    def req_master_update(self) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "master"),
            ""
        )

    def req_bpm_update(self) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "bpm"),
            ""
        )
