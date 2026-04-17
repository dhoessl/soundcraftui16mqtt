from loguru import logger
from os import path
from re import match

from . import DBConnection as DBC
from soundcraftui16mqtt_mqtt import MqttClient


class DatabaseMqttController(MqttClient):
    """ Class to run a Mqtt Client setting new data in database and serving
    Requests to this database values.
    The moment a new value is set in the database it also gets send to clients
    listening for requests.
    """
    DENIED_OPTIONS = ["digitech", "deesser", "aux", "gate", "eq", "dyn"]
    ALLOWED_INPUT_FUNCTIONS = ["mix", "mute", "solo", "gain"]
    ALLOWED_FX_FUNCTIONS = ["mix", "mute"]

    def __init__(
        self, run_forever: bool = False, host: str = "localhost",
        port: int = 1883
    ) -> None:
        super().__init__()
        self.runforever = run_forever
        self.db = DBC()
        self.listen_topics = [
            "config", "database_request", "status_request", "status_report",
            "endpoint_request", "endpoint_report"
        ]
        self.database_update_topic = "database_update"
        self.status_update_topic = "status_update"
        self.endpoint_update_topic = "endpoint_update"

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        for topic in self.listen_topics:
            self.client.subscribe(f"{topic}/#")
            logger.debug(f"Controller connected to {topic}/#")

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        decoded_msg = self._message_decoder(msg.payload.decode())
        if topic.startswith(self.listen_topics[0]):
            command = path.split(topic)[1]
            if command not in ["master", "i", "f"]:
                logger.debug(f"Skipped (command): {topic} => {decoded_msg}")
            elif (
                "option" in decoded_msg
                and "option" in decoded_msg
                and decoded_msg["option"] in self.DENIED_OPTIONS
            ):
                logger.debug(f"Skipped (option): {topic} => {decoded_msg}")
            elif command == "master":
                self.master_update(decoded_msg["value"])
            elif (
                command == "f"
                and "function" in decoded_msg
                and decoded_msg["function"] == "bpm"
            ):
                self.bpm_update(decoded_msg["value"])
            elif (
                command == "i" and "channel" in decoded_msg
                and "option" in decoded_msg and decoded_msg["option"] == "fx"
            ):
                self.channel_fx_update(decoded_msg)
            elif (
                command == "i" and "channel" in decoded_msg
                and "function" in decoded_msg
                and decoded_msg["function"] in self.ALLOWED_INPUT_FUNCTIONS
            ):
                self.channel_update(decoded_msg)
            elif (
                command == "f" and "function" in decoded_msg
                and (
                    decoded_msg["function"] in self.ALLOWED_FX_FUNCTIONS
                    or match(r"^par\d$", decoded_msg["function"])
                )
            ):
                self.fx_update(decoded_msg)
            else:
                logger.debug(f"Unsolved: {topic} => {decoded_msg}")
        elif topic.startswith(self.listen_topics[1]):
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
        elif topic.startswith(self.listen_topics[2]):
            self.publish_status(path.split(topic)[1])
        elif topic.startswith(self.listen_topics[3]):
            self.update_status(decoded_msg)
        elif topic.startswith(self.listen_topics[4]):
            self.publish_endpoints(path.split(topic)[1])
        elif topic.startswith(self.listen_topics[5]):
            self.update_endpoints(decoded_msg)
        else:
            logger.debug(f"Unsolved: {topic} => {decoded_msg}")

    def master_update(self, msg: str | float) -> None:
        self.db.execute(
            "UPDATE misc SET value = :value WHERE parameter = 'master'",
            {
                "value": float(msg)
            },
            True
        )
        self.publish_master("all")

    def bpm_update(self, msg: str | float) -> None:
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
            f"UPDATE fx SET {msg['function']} = :value WHERE id = :fx",
            {
                "value": float(msg["value"]),
                "fx": msg["channel"]
            },
            True
        )
        self.publish_fx(
            {
                "param": msg["function"],
                "fx": msg["channel"]
            },
            "all"
        )

    def channel_update(self, msg: dict) -> None:
        self.db.execute(
            f"UPDATE channel SET {msg['function']} = :value "
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
                "param": msg["function"]
            },
            "all"
        )

    def channel_fx_update(self, msg: dict) -> None:
        self.db.execute(
            f"UPDATE channel_fx SET {msg['function']} = :value "
            "WHERE channel_id = :channel AND fx_id = :fx",
            {
                "value": float(msg["value"]),
                "channel": msg["channel"],
                "fx": msg["option_channel"]
            },
            True
        )
        self.publish_channel_fx(
            {
                "channel": msg["channel"],
                "fx": msg["option_channel"],
                "param": msg["function"]
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

    def update_status(self, data: dict) -> None:
        if (
            "state" not in data
            or data["state"] not in [True, False, 1, 0]
        ):
            return None
        self.db.execute(
            "UPDATE status SET state = :state WHERE name = :name",
            {"state": int(data["state"]), "name": data["name"]},
            True
        )
        self.publish_status("all")

    def publish_status(self, requester: str) -> None:
        rows = self.db.execute("SELECT name, state FROM status")
        status_dict = {}
        for row in rows:
            status_dict[row[0]] = row[1]
        self.client.publish(
            path.join(self.status_update_topic, requester),
            self._message_encode(status_dict)
        )

    def update_endpoints(self, data: dict) -> None:
        self.db.execute(
            "UPDATE entity_config SET address = :address, port = :port "
            "WHERE name = :name",
            {
                "name": data["name"],
                "address": data["address"],
                "port": data["port"]
            },
            True
        )
        self.publish_endpoints("all")

    def publish_endpoints(self, requester: str) -> None:
        rows = self.db.execute("SELECT name, address, port FROM entity_config")
        endpoints = {}
        for row in rows:
            endpoints[row[0]] = {
                "address": row[1],
                "port": row[2]
            }
        self.client.publish(
            path.join(self.endpoint_update_topic, requester),
            self._message_encode(endpoints)
        )
