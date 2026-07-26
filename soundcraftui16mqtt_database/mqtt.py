from loguru import logger
from os import path
from re import match

from . import DBConnection as DBC
from soundcraftui16mqtt_mqtt import MqttClient
from soundcraftui16mqtt_mixer import (
    power_format, percent_format, delay_time_format, room_time_format,
    mix_format
)


class DatabaseMqttController(MqttClient):
    """ Class to run a Mqtt Client to set new data in database and serving
    Requests of this database values.
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
            "endpoint_request", "endpoint_report", "preset_request",
            "preset_edit"
        ]
        self.database_update_topic = "database_update"
        self.status_update_topic = "status_update"
        self.endpoint_update_topic = "endpoint_update"
        self.preset_update_topic = "preset_update"

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
        elif topic.startswith(self.listen_topics[6]):
            self.publish_preset(requester)
        elif topic.startswith(self.listen_topics[7]):
            if "action" in decoded_msg and decoded_msg["action"] == "create":
                self.create_preset(decoded_msg)
            elif "action" in decoded_msg and decoded_msg["action"] == "delete":
                self.delete_preset(decoded_msg)
            else:
                logger.debug(
                    f"Could not determine perset action... {decoded_msg}"
                )
        else:
            logger.debug(f"Unsolved: {topic} => {decoded_msg}")

    def _format_freq(self, freq: float) -> str:
        if freq >= 10000:
            return f"{freq/1000:.1f}kHz"
        elif freq >= 1000:
            return f"{freq/1000:.2f}kHz"
        else:
            return f"{freq:.0f}Hz"

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
            self._message_encode({
                "value": rows[0][0],
                "value_formated": f"{mix_format(rows[0][0]):.1f} dB"
            })
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
        if str(msg["fx"]) == "1" and msg["param"] == "par1":
            value_formated = f"{delay_time_format(rows[0][0]):.0f}ms"
        elif str(msg["fx"]) == "3" and msg["param"] == "par1":
            value_formated = f"{room_time_format(rows[0][0]):.0f}ms"
        elif (
            (
                str(msg["fx"]) == "0"
                and (msg["param"] == "par2" or msg["param"] == "par3")
            )
            or (str(msg["fx"]) == "1" and msg["param"] == "par3")
            or (str(msg["fx"]) == "2" and msg["param"] == "par2")
            or (
                str(msg["fx"]) == "3"
                and (msg["param"] == "par2" or msg["param"] == "par3")
            )
        ):
            value_formated = f"{percent_format(rows[0][0], 0, 100):.0f}%"
        elif str(msg["fx"]) == "1" and msg["param"] == "par2":
            value_formated = f"{percent_format(rows[0][0], 0, 200):.0f}%"
        elif str(msg["fx"]) == "0" and msg["param"] == "par1":
            value_formated = f"{power_format(rows[0][0], 300, 8000):.0f}ms"
        elif (
            str(msg["fx"]) == "0" and msg["param"] == "par4"
            or str(msg["fx"]) == "2" and msg["param"] == "par3"
            or str(msg["fx"]) == "3" and msg["param"] == "par4"
        ):
            value_formated = self._format_freq(
                power_format(rows[0][0], 400, 22000)
            )
        elif (
            str(msg["fx"]) == "0" and msg["param"] == "par5"
            or str(msg["fx"]) == "3" and msg["param"] == "par5"
        ):
            value_formated = self._format_freq(
                power_format(rows[0][0], 20, 5000)
            )
        elif str(msg["fx"]) == "1" and msg["param"] == "par4":
            value_formated = self._format_freq(
                power_format(rows[0][0], 20, 22000)
            )
        elif str(msg["fx"]) == "2" and msg["param"] == "par1":
            value_formated = f"{percent_format(rows[0][0], -100, 100):.0f}c"
        elif msg["param"] == "mix":
            value_formated = f"{mix_format(rows[0][0]):.1f}"
        elif msg["param"] == "mute":
            value_formated = rows[0][0]
        else:
            logger.warning(
                f"Could not format fx {msg['fx']} param {msg['param']}"
            )
            value_formated = rows[0][0]
        self.client.publish(
            path.join(self.database_update_topic, requester, "fx"),
            self._message_encode(
                {
                    "fx": msg["fx"],
                    "param": msg["param"],
                    "value": rows[0][0],
                    "value_formated": value_formated
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
                    "value": rows[0][0],
                    "value_formated": f"{mix_format(rows[0][0]):.1f}dB"
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
                    "value": rows[0][0],
                    "value_formated": f"{mix_format(rows[0][0]):.1f}dB"
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

    def create_preset(self, msg: dict) -> None:
        for fx in msg["fx"]:
            fx_data = msg["fx"][fx]
            self.db.execute(
                "INSERT INTO fx_preset(preset, fx_id, par1, par2, par3, par4, "
                "par5, mute, mix) VALUES (:preset, :fx_id, :par1, :par2, "
                ":par3, :par4, :par5, :par6, :mute, :mix)",
                {
                    "preset": msg["id"],
                    "fx_id": fx,
                    "par1": fx_data["par1"],
                    "par2": fx_data["par2"],
                    "par3": fx_data["par3"],
                    "par4": fx_data["par4"],
                    "par5": fx_data["par5"],
                    "par6": fx_data["par6"] if "par6" in fx_data else 0,
                    "mute": fx_data["mute"],
                    "mix": fx_data["mix"]
                },
                True
            )
        for channel in msg["channel_fx"]:
            for fx in msg["channel_fx"][channel]:
                channel_fx = msg["channel_fx"][channel][fx]
                self.db.execute(
                    "INSERT INTO channel_fx_preset (preset, channel_id, "
                    "fx_id, value, mute) VALUES (:preset, :channel_id, "
                    ":fx_id, :value :mute)",
                    {
                        "preset": msg["id"],
                        "channel_id": channel,
                        "fx_id": fx,
                        "value": channel_fx["value"],
                        "mute": channel_fx["mute"]
                    },
                    True
                )
        self.publish_preset("all")

    def delete_preset(self, msg: dict) -> None:
        self.db.execute(
            "DELETE FROM fx_preset WHERE preset = :preset",
            {"preset": msg["id"]},
            True
        )
        self.db.execute(
            "DELETE FROM channel_fx_preset WHERE preset = :preset",
            {"preset": msg["id"]},
            True
        )
        self.publish_preset("all")

    def _create_preset_skel(self) -> dict:
        skel = {"fx": {}, "channel": {}}
        for ch in range(12):
            skel["channel"][ch] = {}
            for fx in range(4):
                skel["channel"][ch][fx] = {
                    "value": None,
                    "mute": None
                }
        return skel

    def publish_preset(self, requester: str) -> None:
        presets = {}
        rows = self.db.execute(
            "SELECT preset, fx_id, par1, par2, par3, par4, par5, par6, mute, "
            "mix "
            "FROM fx_preset"
        )
        for row in rows:
            if row[0] not in presets:
                presets[row[0]] = self._create_preset_skel()
            presets[row[0]]["fx"][row[1]] = {
                "par1": row[2],
                "par2": row[3],
                "par3": row[4],
                "par4": row[5],
                "par5": row[6],
                "par6": row[7],
                "mute": row[8],
                "mix": row[9]
            }
        rows = self.db.execute(
            "SELECT preset, channel_id, fx_id, value, mute "
            "FROM channel_fx_preset"
        )
        for row in rows:
            if row[0] not in presets:
                presets[row[0]] = self._create_preset_skel()
            presets[row[0]]["channel"][row[1]][row[2]] = {
                "value": row[3],
                "mute": row[4]
            }
        self.client.publish(
            path.join(self.controller_update_topic, requester),
            self._message_encode(presets)
        )
