from loguru import logger
from os import path

from soundcraftui16mqtt_mqtt import MqttClient


class DatabaseMqttListener(MqttClient):
    def __init__(
            self, run_forever: bool = False, host: str = "localhost",
            port: int = 1883, enable_status: bool = False,
            enable_endpoint: bool = False
    ) -> None:
        super().__init__(run_forever, host, port)
        self.request_topic = "database_request"
        self.update_topic = "database_update"
        self.request_status_topic = "status_request"
        self.send_status_topic = "status_report"
        self.update_status_topic = "status_update"
        self.request_endpoint_topic = "endpoint_request"
        self.send_endpoint_topic = "endpoint_report"
        self.update_endpoint_topic = "endpoint_update"
        self.enable_status_updates = enable_status
        self.enable_endpoint_updates = enable_endpoint

    def _on_connect(self, client, userdata, flags, reason, prop) -> None:
        self.client.subscribe(f"{self.update_topic}/all/#")
        logger.debug(f"Listener Client connected to {self.update_topic}/all/#")
        self.client.subscribe(f"{self.update_topic}/{self.id}/#")
        logger.debug(
            f"Listener Client connected to {self.update_topic}/{self.id}/#"
        )
        if self.enable_status_updates:
            self.client.subscribe(f"{self.update_status_topic}/all")
            self.client.subscribe(f"{self.update_status_topic}/{self.id}")
            logger.debug(
                "Listener Client connected to "
                f"{self.update_status_topic}/{self.id} and "
                f"{self.update_status_topic}/all"
            )
        if self.enable_endpoint_updates:
            self.client.subscribe(f"{self.update_endpoint_topic}/all")
            self.client.subscribe(f"{self.update_endpoint_topic}/{self.id}")
            logger.debug(
                "Listener Client connected to "
                f"{self.update_endpoint_topic}/{self.id} and "
                f"{self.update_endpoint_topic}/all"
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
        elif topic.startswith(self.update_status_topic):
            self.status_update(decoded_msg)
        elif topic.startswith(self.update_endpoint_topic):
            self.endpoint_update(decoded_msg)
        else:
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

    def status_update(self, msg: dict) -> None:
        logger.warning("Please add a status_update(msg) function")
        return None

    def endpoint_update(self, msg: dict) -> None:
        logger.warning("Please add a endpoint_update(msg) function")
        return None

    def req_channel_update(self, param: str, channel: int | str) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "channel"),
            self._message_encode(
                {
                    "channel": str(channel),
                    "param": param
                }
            )
        )

    def req_channel_fx_update(
        self, param: str, fx_id: int | str, channel: int | str
    ) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "channel_fx"),
            self._message_encode(
                {
                    "channel": str(channel),
                    "fx": str(fx_id),
                    "param": param
                }
            )
        )

    def req_fx_update(self, param: str, fx_id: int | str) -> None:
        self.client.publish(
            path.join(self.request_topic, self.id, "fx"),
            self._message_encode(
                {
                    "fx": str(fx_id),
                    "param": param
                }
            )
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

    def req_status(self) -> None:
        self.client.publish(
            path.join(self.request_status_topic, self.id),
            ""
        )

    def req_endpoints(self) -> None:
        self.client.publish(
            path.join(self.request_endpoint_topic, self.id),
            ""
        )

    def send_status(self, entity: str, state: bool) -> None:
        self.client.publish(
            path.join(self.send_status_topic, self.id),
            self._encode_message({
                "state": state,
                "name": entity
            })
        )

    def send_endpoint(self, entity: str, address: str, port: int) -> None:
        self.client.publish(
            path.join(self.send_endpoint_topic, self.id),
            self._encode_message({
                "name": entity,
                "address": address,
                "port": port
            })
        )
