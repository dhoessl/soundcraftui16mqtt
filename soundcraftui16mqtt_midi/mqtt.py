from __future__ import annotations
from typing import TYPE_CHECKING

from os import path
from loguru import logger
from datetime import datetime, UTC

from soundcraftui16mqtt_mqtt import MqttClient

if TYPE_CHECKING:
    from .apc import APC
    from .midimix import MIDIMix


class MidiMqttClient(MqttClient):
    def __init__(
        self, host: str, port: int, controller: APC | MIDIMix
    ) -> None:
        self.controller = controller  # connected Controller
        # Listen topics for updates
        self.topics = ["database", "status", "endpoint", "preset"]
        # Topics to send updates to
        self.endpoint_report_topic = "endpoint_report"
        self.preset_edit_topic = "preset_edit"
        # Topics to request updates/information from
        self.database_request_topic = "database_request"
        self.status_request_topic = "status_request"
        self.endpoint_request_topic = "endpoint_request"
        self.preset_request_topic = "preset_request"
        # Midi controller communication topic
        self.midi_coms_topic = "midi_com"
        # Init the MqttClient
        super().__init__(host=host, port=port)

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        # Connect to update topics
        for topic in self.topics:
            self.client.subscribe(f"{topic}_update/all/#")
            self.client.subscribe(f"{topic}_update/{self.id}/#")
            logger.debug(
                f"{self.controller.name} mqtt client connected to "
                f"{topic}_update"
            )
        # connect to midi com topic
        self.client.subscribe(f"{self.midi_coms_topic}/#")
        logger.debug(f"{self.controller.name} mqtt midi com channel connected")
        # Setup complete
        logger.debug(
            f"{self.controller.name} mqtt client setup complete and online"
        )
        self.send_alive()

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        new_msg = self._message_decoder(msg.payload.decode())
        # Database Update message
        if topic.startswith(f"{self.topics[0]}_update"):
            if path.split(topic)[1] == "channel":
                self.controller.channel_update(new_msg)
            elif path.split(topic)[1] == "channel_fx":
                self.controller.channel_fx_update(new_msg)
            elif path.split(topic)[1] == "fx":
                self.controller.fx_update(new_msg)
            elif path.split(topic)[1] == "master":
                self.controller.master_update(new_msg)
            elif path.split(topic)[1] == "bpm":
                self.controller.bpm_update(new_msg)
            else:
                logger.debug(
                    f"{self.controller.name} Mqtt - Unsolved: {topic} -> "
                    f"{new_msg}"
                )
        elif topic.startswith(f"{self.topics[1]}_update"):
            # Status Update message
            self.controller.status_update(new_msg)
        elif topic.startswith(f"{self.topics[2]}_update"):
            # Endpoint Update message
            self.controller.endpoints_update(new_msg)
        elif topic.startswith(f"{self.topics[3]}_update"):
            # Preset Update message
            pass  # TODO: define controller actions for preset update
        elif topic.startswith(f"{self.midi_coms_topic}"):
            if path.split(topic)[-1] == str(self.id):
                # Messages from self can be ignored
                pass
            self.handle_midi_com(new_msg)
        else:
            logger.debug(
                f"{self.controller.name} Mqtt - Not handled: {topic} -> "
                f"{new_msg}"
            )

    def _handle_midi_com(self, msg: dict) -> None:
        if "kind" in msg and msg["kind"] == "alive":
            # Update connected device info
            if msg["id"] not in self.controller.connected_devices:
                self.controller.connected_devices[msg["id"]] = {
                    "last_seen": datetime.fromtimestamp(
                        msg["timestamp"], tz=UTC
                    )
                }
            else:
                self.controller.connected_devices[msg["id"]]["last_seen"] = \
                    datetime.fromtimestamp(msg["timestamp"], tz=UTC)
        else:
            self.controller.handle_midi_com(msg)

    def send_alive(self) -> None:
        self.client.publish(
            self.send_midi_com_message({
                "kind": "alive",
                "name": self.controller.name,
                "id": self.controller.id,
                "timestamp": datetime.now(UTC).timestamp()
            })
        )

    def send_midi_com_message(self, data: dict) -> None:
        self.client.publish(
            f"{self.midi_coms_topic}/{self.id}",
            self._message_encode(data)
        )

    def request_midimix_config(self) -> None:
        base_request_path = path.join(self.database_request_topic, self.id)
        self.client.publish(
            path.join(base_request_path, "master"),
            self._message_encode("")
        )
        self.client.publish(
            path.join(base_request_path, "bpm"),
            self._message_encode("")
        )
        for channel in range(8, 12):
            for param in ["mix", "mute", "gain"]:
                self.client.publish(
                    path.join(base_request_path, "channel"),
                    self._message_encode({
                        "param": param,
                        "channel": channel
                    })
                )
        for par in range(1, 4):
            self.client.publish(
                path.join(base_request_path, "fx"),
                self._message_encode({
                    "param": f"par{par}",
                    "fx": 2
                })
            )
        for par in range(1, 6):
            self.client.publish(
                path.join(base_request_path, "fx"),
                self._message_encode({
                    "param": f"par{par}",
                    "fx": 4
                })
            )
        for channel in range(12):
            for fx in range(4):
                for param in ["mute", "value"]:
                    self.client.publish(
                        path.join(base_request_path, "channel_fx"),
                        self._message_encode({
                            "channel": channel,
                            "fx": fx,
                            "param": param
                        })
                    )

    def request_apc_config(self) -> None:
        base_request_path = path.join(self.database_request_topic, self.id)
        for channel in range(8):
            for param in ["mix", "mute", "gain"]:
                self.client.publish(
                    path.join(base_request_path, "channel"),
                    self._message_encode({
                        "param": param,
                        "channel": channel
                    })
                )
        for par in range(1, 6):
            self.client.publish(
                path.join(base_request_path, "fx"),
                self._message_encode({
                    "param": f"par{par}",
                    "fx": 0
                })
            )
        for par in range(1, 5):
            self.client.publish(
                path.join(base_request_path, "fx"),
                self._message_encode({
                    "param": f"par{par}",
                    "fx": 1
                })
            )
        self.client.publish(
            path.join(base_request_path, "preset_request"),
            self._message_encode("")
        )

    def request_status(self) -> None:
        self.client.publish(
            path.join(self.status_request_topic, self.id),
            self.client._message_encode("")
        )

    def request_endpoints(self) -> None:
        self.client.publish(
            path.join(self.endpoint_request_topic, self.id),
            self.client._message_encode("")
        )
