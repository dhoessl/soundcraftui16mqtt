from akai_pro_py.controllers import APCMinimkii as APCmk2
from mido import get_input_names  # noqa: F401
from loguru import logger
from datetime import datetime, UTC  # noqa: F401
from time import sleep
from threading import Thread, Event

from .soundcraftui16mqtt_mqtt import MidiMqttClient
from .soundcraftui16mqtt_mixer import MixerSender, midi_to_soundcraft_format

"""
APC has 8 pages in total 0 - 7
Page 1 and 2 are Preset Pages on Grid
Page 1 fader
    0  - (8) channel mix
Page 2 fader
    0  - 4  reverb fx
    5  - 8  delay fx
"""


class APC(APCmk2):
    def __init__(
        self, midi_string: str, mqtt_host: str, mqtt_port: int = 1883
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.ready_dispatch = self.on_ready
        self.event_dispatch = self.on_event
        self.id = "APC"
        self.connected_devices = {
            "mixer": {
                "address": None,
                "port": None,
                "state": False
            }
        }
        self.ready = False
        self.shift = False
        self.page = 0
        self.mixer_config = self._skel_config()
        self.presets = None
        self.mqtt = MidiMqttClient(mqtt_host, mqtt_port, self)
        self.mixer = None
        self.alive_thread = Thread(
            target=self._alive_thread,
            args=()
        )
        self.exit_flag = Event()

    def is_alive(self) -> bool:
        return True if self.midi_in.name in get_input_names else False

    def stop(self) -> None:
        self.mqtt.stop()
        if self.alive_thread.is_alive():
            if not self.exit_flag.is_set():
                self.exit_flag.set()
            self.alive_thread.join()
            if self.mixer:
                self.mixer.stop()
        logger.info(f"Midi Controller {self.name} stopped")

    def on_ready(self) -> None:
        self.mqtt.start()
        self.alive_thread.start()
        self.mqtt.request_apc_config()
        self.mqtt.request_status()
        self.mqtt.request_endpoints()
        self.ready = True
        logger.debug(f"Midi Controller {self.name} is ready")

    def on_event(
        self, event: APCmk2.GridButton | APCmk2.SideButton | APCmk2.LowerButton
        | APCmk2.Fader | APCmk2.ShiftButton
    ) -> None:
        if isinstance(event, APCmk2.GridButton):
            self._on_gridbutton_event(event)
        elif isinstance(event, APCmk2.SideButton):
            self._on_sidebutton_event(event)
        elif isinstance(event, APCmk2.LowerButton):
            self._on_lowerbutton_event(event)
        elif isinstance(event, APCmk2.Fader):
            self._on_fader_event(event)
        elif isinstance(event, APCmk2.ShiftButton):
            self._on_shift_event(event)
        else:
            logger.warning(f"Unkown Event {event} on controller {self.name}")

    def _on_gridbutton_event(self, event: APCmk2.GridButton) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")
        if not event.state:
            # Do not care about release event
            return None
        if self.page in [0, 1]:
            # Preset Pages
            pass
        return None

    def _on_sidebutton_event(self, event: APCmk2.SideButton) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")
        # Update page if not shift
        if self.shift:
            return None
        if self.page != event.button_id:
            self.page = event.button_id
            self._send_page_update()

    def _on_lowerbutton_event(self, event: APCmk2.LowerButton) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")
        # Mute channel faders
        if not event.state:
            return None
        if self.page == 0:
            # (un)mute channel
            self.mixer.mute(
                "i",
                event.button_id,
                int(
                    not
                    self.mixer_config["channels"][str(event.button_id)]["mute"]
                )
            )
        elif self.page == 1:
            # No actions for fx setting mode
            pass

    def _on_fader_event(self, event: APCmk2.Fader) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")
        if self.page == 0:
            self.mixer.mix(
                "i",
                event.fader_id,
                midi_to_soundcraft_format(event.value)
            )
        elif self.page == 1 and event.fader_id in range(5):
            self.mixer.fx_setting(
                "0",
                event.fader_id + 1,
                midi_to_soundcraft_format(event.value)
            )
        elif self.page == 1 and event.fader_id in range(5, 9):
            self.mixer.fx_setting(
                "1",
                event.fader_id - 4,
                midi_to_soundcraft_format(event.value)
            )
        else:
            # No actions defined right now
            return None

    def _on_shift_event(self, event: APCmk2.ShiftButton) -> None:
        self.shift = True if event.state else False

    def channel_update(self, msg: dict) -> None:
        if int(msg["channel"]) not in range(8):
            # Channel is not on apc
            return None
        if msg["param"] not in self.mixer_config["channels"][str(msg["channel"])]:  # noqa: E501
            # parameter is not used on apc
            return None
        self.mixer_config["channels"][str(msg["channel"])][msg["param"]] = \
            msg["value"]

    def fx_update(self, msg: dict) -> None:
        if int(msg["fx"]) not in [0, 1]:
            # Other fx not on apc
            return None
        if msg["param"] not in self.mixer_config["fx"][str(msg["fx"])]:
            # Ignore all params expect for skel created ones
            return None
        self.mixer_config["fx"][str(msg["fx"])][msg["param"]] = msg["value"]

    def channel_fx_update(self, msg: dict) -> None:
        # Not used on apc
        return None

    def master_update(self, msg: dict) -> None:
        # Not used on apc
        return None

    def bpm_update(self, msg: str | int) -> None:
        # Not used on apc
        return None

    def handle_midi_com(self, msg: dict) -> None:
        if "kind" in msg and msg["kind"] == "page":
            if msg["page"] == "request":
                self._send_page_update()

    def _send_page_update(self) -> None:
        self.mqtt.send_midi_com_message({
            "kind": "page",
            "page": self.page
        })

    def _alive_thread(self) -> None:
        while not self.exit_flag.is_set():
            if self.is_alive():
                self.mqtt.send_alive()
            else:
                logger.warning(f"{self.name} not alive?")
                continue
            if (
                not self.mixer
                and self.connected_devices["mixer"]["state"]
                and self.connected_devices["mixer"]["address"]
            ):
                self.mixer = MixerSender(
                    str(self.connected_devices["mixer"]["address"]),
                    int(self.connected_devices["mixer"]["port"])
                )
                self.mixer.start()
            elif (
                self.mixer
                and not self.mixer.connected
            ):
                self.mixer.stop()
                self.mixer = MixerSender(
                    str(self.connected_devices["mixer"]["address"]),
                    int(self.connected_devices["mixer"]["port"])
                )
                self.mixer.start()
            sleep(5)

    def _skel_config(self) -> dict:
        config = {
            "channels": {},
            "fx": {
                "0": {
                    "par1": None,
                    "par2": None,
                    "par3": None,
                    "par4": None,
                    "Par5": None,
                },
                "1": {
                    "par1": None,
                    "par2": None,
                    "par3": None,
                    "par4": None
                }
            }
        }
        for channel in range(8):
            config["channels"][str(channel)] = {
                "mix": None,
                "mute": None,
                "gain": None
            }
        return config

    def endpoints_update(self, msg: dict) -> None:
        if "mixer" in msg:
            self.connected_devices["mixer"]["address"] = \
                msg["mixer"]["address"]
            self.connected_devices["mixer"]["port"] = msg["mixer"]["port"]

    def status_update(self, msg: dict) -> None:
        if "mixer" in msg:
            self.connected_devices["mixer"]["state"] = msg["mixer"]
