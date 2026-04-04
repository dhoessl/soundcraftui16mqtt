#!/usr/bin/env python3

from loguru import logger
from os import path

from . import DBConnection as DBC
from soundcraftui16mqtt_mqtt import MqttClient


class DatabaseMqttController(MqttClient):
    """ Class to run a Mqtt Client setting new data in database and serving
    Requests to this database values.
    The moment a new value is set in the database it also gets send to clients
    listening for requests.
    """
    def __init__(
        self, run_forever: bool = False, host: str = "localhost",
        port: int = 1883
    ) -> None:
        super().__init__()
        self.runforever = run_forever
        self.db = DBC()
        self.listen_topics = ["config", "database_request"]
        self.database_update_topic = "database_update"

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        for topic in self.listen_topic:
            self.client.subscribe(f"{topic}/#")
            logger.debug(f"Controller connected to {topic}/#")

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        decoded_msg = self._message_decoder(msg.payload.decode())
        if topic.startswith(self.sub_topics[0]):
            command = path.split(topic)[1]
            if command == "channel":
                self.channel_update(decoded_msg)
            elif command == "channel_fx":
                self.channel_fx_update(decoded_msg)
            elif command == "fx":
                self.fx_update(decoded_msg)
            elif command == "master":
                self.master_update(decoded_msg)
            elif command == "bpm":
                self.bpm_update(decoded_msg)
            else:
                logger.debug(f"Unsolved: {topic} => {decoded_msg}")
        elif topic.startswith(self.sub_topics[1]):
            remaining_topic, command = path.split(topic)
            requester = path.split(remaining_topic)[1]
            if command == "channel":
                self.publish_channel(decoded_msg, requester)
            elif command == "channel_fx":
                self.publish_channel_fx(decoded_msg, requester)
            elif command == "fx":
                self.publish_fx(decoded_msg, requester)
            elif command == "master":
                self.publish_master(requester)
            elif command == "bpm":
                self.publish_bpm(requester)
            else:
                logger.debug(f"Unsolved: {topic} => {decoded_msg}")
        else:
            logger.debug(f"Unsolved: {topic} => {decoded_msg}")

    def master_update(self, msg: float) -> None:
        self.db.execute(
            "UPDATE misc SET value = :value WHERE parameter = 'master'",
            {
                "value": float(msg)
            },
            True
        )
        self.publish_master("all")

    def bpm_update(self, msg: float) -> None:
        self.db.execute(
            "UPDATE misc SET value = :value WHERE parameter = 'bpm'",
            {
                "value": float(msg)
            },
            True
        )
        self.publish_bpm("all")

    def fx_update(self, msg: dict) -> None:
        self.db.execute(
            f"UPDATE fx SET {msg['param']} = :value WHERE id = :fx",
            {
                "value": float(msg["value"]),
                "fx": msg["fx"]
            },
            True
        )
        self.publish_fx({"param": msg["param"], "fx": msg["fx"]}, "all")

    def channel_update(self, msg: dict) -> None:
        self.db.execute(
            f"UPDATE channel SET {msg['param']} = :value "
            "WHERE id = :channel",
            {
                "value": float(msg["value"]),
                "channel": msg["channel"]
            },
            True
        )
        self.publish_channel(
            {
                "channel": msg["channel"],
                "param": msg["param"]
            },
            "all"
        )

    def channel_fx_update(self, msg: dict) -> None:
        self.db.execute(
            f"UPDATE channel_fx SET {msg['param']} = :value "
            "WHERE channel_id = :channel AND fx_id = :fx",
            {
                "value": float(msg["value"]),
                "channel": msg["channel"],
                "fx": msg["fx"]
            },
            True
        )
        self.publish_channel_fx(
            {
                "channel": msg["channel"],
                "fx": msg["fx"],
                "param": msg["param"]
            },
            "all"
        )

    def publish_master(self, requester: str) -> None:
        rows = self.db.execute(
            "SELECT value FROM misc WHERE parameter = 'master'"
        )
        self.client.publish(
            path.join(self.database_update_topic, requester, "master"),
            rows[0][0]
        )

    def publish_bpm(self, requester: str) -> None:
        rows = self.db.execute(
            "SELECT value FROM misc WHERE parameter = 'bpm'"
        )
        self.client.publish(
            path.join(self.database_update_topic, requester, "bpm"),
            rows[0][0]
        )

    def publish_fx(self, msg: dict, requester: str) -> None:
        rows = self.db.execute(
            f"SELECT {msg['param']} FROM fx WHERE id = :fx",
            {"fx": msg["fx"]}
        )
        self.client.publish(
            path.join(self.database_update_topic, requester, "fx"),
            self._message_encode(
                {
                    "fx": msg["fx"],
                    "param": msg["param"],
                    "value": rows[0][0]
                }
            )
        )

    def publish_channel(self, msg: dict, requester: str) -> None:
        rows = self.db.execute(
            f"SELECT {msg['param']} FROM channel WHERE id = :channel",
            {"channel": msg["channel"]}
        )
        self.client.publish(
            path.join(self.database_update_topic, requester, "channel"),
            self._message_encode(
                {
                    "channel": msg["channel"],
                    "param": msg["param"],
                    "value": rows[0][0]
                }
            )
        )

    def publish_channel_fx(self, msg: dict, requester: str) -> None:
        rows = self.db.execute(
            f"SELECT {msg['param']} FROM channel_fx "
            "WHERE channel_id = :channel AND fx_id = :fx",
            {"channel": msg["channel"], "fx": msg["fx"]}
        )
        self.client.publish(
            path.join(self.database_update_topic, requester, "channel_fx"),
            self._message_encode(
                {
                    "channel": msg["channel"],
                    "fx": msg["fx"],
                    "param": msg["param"],
                    "value": rows[0][0]
                }
            )
        )
