#!/usr/bin/env python3

from loguru import logger
from json import loads, JSONDecodeError, dumps  # noqa: F401
from os import path

from . import DBConnection as DBC
from soundcraftui16mqtt_mqtt import MqttClient


class DatabaseMqttController(MqttClient):
    """ Class to run a Mqtt Client setting new data in database and serving
    Requests to this database values.
    The moment a new value is set in the database it also gets send to clients
    listening for requests.
    """
    def __init__(self, run_forever: bool = False) -> None:
        super().__init__()
        self.runforever = run_forever
        self.db = DBC()
        self.sub_topics = ["config", "database"]

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        for topic in self.sub_topics:
            self.client.subscribe(f"{topic}/#")
        logger.debug("Controller Client Connected")

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        decoded_msg = self._message_decoder(msg.payload.decode())
        if topic.startswith(self.sub_topics[0]):
            if path.split(topic)[1] == "channel":
                self.channel_update(path.split(topic)[0], decoded_msg)
            elif path.split(topic)[1] == "fx":
                self.fx_update(path.split(topic)[0], decoded_msg)
            elif path.split(topic)[1] == "master":
                self.master_update(decoded_msg)
            elif path.split(topic)[1] == "bpm":
                self.bpm_update(decoded_msg)
            logger.debug(f"Update Config. Topic {topic} => {decoded_msg}")
            return None
        if topic.startswith(self.sub_topics[1]) and decoded_msg == "dbreq":
            if path.split(topic)[1] == "channel":
                self.publish_channel(path.split(topic)[0])
            elif path.split(topic)[1] == "fx":
                self.publish_fx(path.split(topic)[0])
            elif path.split(topic)[1] == "master":
                self.publish_master()
            elif path.split(topic)[1] == "bpm":
                self.publish_bpm()
            logger.debug(f"Handling Request. Topic {topic} => {decoded_msg}")
            return None
        logger.debug(f"Unsolved msg: {topic} => {decoded_msg}")

    def master_update(self, msg: float) -> bool:
        self.db.execute(
            "UPDATE misc SET value = :value WHERE parameter = 'master'",
            {"value": float(msg)},
            True
        )
        return True

    def publish_master(self) -> None:
        rows = self.db.execute(
            "SELECT value FROM misc WHERE parameter = 'master'"
        )
        self.client.publish(
            path.join(self.sub_topics[1], "master"),
            rows[0][0]
        )

    def bpm_update(self, msg: float) -> bool:
        self.db.execute(
            "UPDATE misc SET value = :value WHERE parameter = 'bpm'",
            {"value": float(msg)},
            True
        )
        return True

    def publish_bpm(self) -> None:
        rows = self.db.execute(
            "SELECT value FROM misc WHERE parameter = 'bpm'"
        )
        self.client.publish(
            path.join(self.sub_topics[1], "bpm"),
            rows[0][0]
        )

    def fx_update(self, topic: str, msg: float) -> bool:
        remaining_topic, fx = path.split(topic)
        remaining_topic, par = path.split(remaining_topic)
        self.db.execute(
            f"UPDATE fx SET {par} = :value WHERE id = :fx",
            {"value": float(msg), "fx": fx},
            True
        )
        return True

    def publish_fx(self, topic: str) -> None:
        remaining_topic, fx = path.split(topic)
        remaining_topic, par = path.split(remaining_topic)
        rows = self.db.execute(
            f"SELECT {par} FROM fx WHERE id = :fx",
            {"fx": fx}
        )
        self.client.publish(
            path.join(self.sub_topics[1], par, fx, "fx"),
            rows[0][0]
        )

    def channel_update(self, topic: str, msg: float) -> bool:
        remaining_topic, channel = path.split(topic)
        remaining_topic, parameter = path.split(remaining_topic)
        if parameter == "fx":
            return self.channel_fx_update(int(channel), remaining_topic, msg)
        self.db.execute(
            f"UPDATE channel SET {parameter} = :value "
            "WHERE id = :channel",
            {"value": float(msg), "channel": channel},
            True
        )

    def publish_channel(self, topic: str) -> None:
        remaining_topic, channel = path.split(topic)
        remaining_topic, parameter = path.split(remaining_topic)
        if parameter == "fx":
            self.publish_channel_fx(int(channel), remaining_topic)
            return None
        rows = self.db.execute(
            f"SELECT {parameter} FROM channel WHERE id = :channel",
            {"channel": channel}
        )
        self.client.publish(
            path.join(self.sub_topics[1], parameter, str(channel), "channel"),
            rows[0][0]
        )

    def channel_fx_update(self, channel: int, topic: str, msg: float) -> bool:
        remaining_topic, fx = path.split(topic)
        remaining_topic, parameter = path.split(remaining_topic)
        self.db.execute(
            f"UPDATE channel_fx SET {parameter} = :value "
            "WHERE channel_id = :channel AND fx_id = :fx",
            {"value": float(msg), "channel": channel, "fx": fx},
            True
        )
        return True

    def publish_channel_fx(self, channel: int | str, topic: str) -> None:
        remaining_topic, fx = path.split(topic)
        remaining_topic, parameter = path.split(remaining_topic)
        rows = self.db.execute(
            f"SELECT {parameter} FROM channel_fx WHERE channel_id = :channel "
            "AND fx_id = :fx",
            {"channel": channel, "fx": fx}
        )
        self.client.publish(
            path.join(
                self.sub_topics[1], parameter, str(fx), "fx", str(channel),
                "channel"
            ),
            rows[0][0]
        )


# if __name__ == "__main__":
#     database_mqtt = DatabaseMqttClient()
#     database_mqtt.start()
