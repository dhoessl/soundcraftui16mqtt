#!/usr/bin/env python3

import paho.mqtt.client as mqtt
from json import loads, dumps, JSONDecodeError
from loguru import logger
from uuid import uuid4


class MqttClient:
    def __init__(
        self, run_forever: bool = False, host: str = "localhost",
        port: int = 1883
    ) -> None:
        self.runforever = run_forever
        self.host = host
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.id = str(uuid4())

    def start(self) -> None:
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.connect(self.host, self.port)
        logger.debug(f"Client {self.id} connected!")
        if self.runforever:
            self.client.loop_forever()
        else:
            self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        logger.debug(f"Client {self.id} stopped!")

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        self.client.loop_stop()
        raise RuntimeError("Please set an `on_connect` function for client")

    def _on_message(self, client, userdata, msg) -> None:
        logger.debug("No on_message set. Default Action")
        logger.info(f"{msg.topic} => {msg.payload}")

    def _message_decoder(self, msg: str | dict) -> str | dict:
        # Tries to decode json formated message into dict
        # If its not a string or json formated message it just returns
        # the input
        if type(msg) is str:
            try:
                decoded_msg = loads(msg)
                return decoded_msg
            except JSONDecodeError:
                return msg
        else:
            return msg

    def _message_encode(self, msg: str | dict) -> str:
        # Tries to encode message in json format if its a dict
        # else it just returns the string
        if type(msg) is str:
            return msg
        elif type(msg) is dict:
            return dumps(msg)
        else:
            raise RuntimeError(f"Can not encode {type(msg)}")
