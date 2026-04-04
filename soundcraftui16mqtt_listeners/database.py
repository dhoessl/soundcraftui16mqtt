#!/usr/bin/env python3

from loguru import logger
from os import path
# from json import dumps

from soundcraftui16mqtt_mqtt import MqttClient


class DatabaseMqttListener(MqttClient):
    def __init__(self, run_forever: bool = False) -> None:
        super().__init__()
        self.runforever = run_forever
        self.sub_topics = ["database"]

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        for topic in self.sub_topics:
            self.client.subscribe(f"{topic}/#")
        logger.debug("Listener Client connected")

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        decoded_msg = self._message_decoder(msg.payload.decode())
        if topic.startswith(self.sub_topics[0]) and decoded_msg != "dbreq":
            if path.split(topic)[1] == "channel":
                self.channel_update(path.split(topic)[0], decoded_msg)
            elif path.split(topic)[1] == "fx":
                self.fx_update(path.split(topic)[0], decoded_msg)
            elif path.split(topic)[1] == "master":
                self.master_update(decoded_msg)
            elif path.split(topic)[1] == "bpm":
                self.bpm_update(decoded_msg)
            logger.debug(f"Updating: {topic} => {decoded_msg}")
            return None
        logger.debug(f"Unsolved: {topic} => {decoded_msg}")

    def channel_update(self, topic: str, msg: str) -> None:
        logger.warning("Please set a channel_update(topic, msg) function")
        return None

    def fx_update(self, topic: str, msg: str) -> None:
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
            path.join(self.sub_topics[0], param, str(channel), "channel"),
            "dbreq"
        )

    def req_channel_fx_update(
        self, param: str, fx_id: int | str, channel: int | str
    ) -> None:
        self.client.publish(
            path.join(
                self.sub_topics[0], param, str(fx_id), "fx", str(channel),
                "channel"
            ),
            "dbreq"
        )

    def req_fx_update(
        self, param: str, fx_id: int | str
    ) -> None:
        self.client.publish(
            path.join(
                self.sub_topics[0], param, str(fx_id), "fx"
            ),
            "dbreq"
        )

    def req_master_update(self) -> None:
        self.client.publish(
            path.join(self.sub_topics[0], "master"),
            "dbreq"
        )

    def req_bpm_update(self) -> None:
        self.client.publish(
            path.join(self.sub_topics[0], "bpm"),
            "dbreq"
        )
