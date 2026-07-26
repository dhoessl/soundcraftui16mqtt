from akai_pro_py.controllers import MIDIMix
from mido import get_input_names  # noqa: F401
from loguru import logger
from datetime import datetime, UTC  # noqa: F401
from time import sleep
from threading import Thread, Event

from .soundcraftui16mqtt_mqtt import MidiMqttClient
from .soundcraftui16mqtt_mixer import MixerSender, midi_to_soundcraft_format

"""
MIDIMix has no pages at its own and its served from apc
knobs has two 'pages' and is select by side buttons
knobs toggle between channels 0 - 5 and 6 - 11

apc page 1 and 2 toggle faders between
apc page 1 fader
    9  - 11 channel mix
    12 - 15 aux return mix
         17 master mix
apc page 2 fader
    9  - 11 chorus fx
    12 - 16 room fx
         17 bpm
"""


class MIDIMix(MIDIMix):
    def __init__(
        self, midi_string: str, mqtt_host: str, mqtt_port: int = 1883
    ) -> None:
        super().__init__(midi_string, midi_string)
        self.ready_dispatch = self.on_ready
        self.event_dispatch = self.on_event
        self.id = "MIDIMix"
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
        self.knob_page = 0
        self.mixer_config = None
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
        self.mqtt.request_midimix_config()
        self.mqtt.request_status()
        self.mqtt.request_endpoints()
        self.ready = True
        logger.debug(f"Midi Controller {self.name} is ready")

    def on_event(
        self, event: MIDIMix.Fader | MIDIMix.Knob | MIDIMix.MuteButton |
        MIDIMix.RecArmButton | MIDIMix.BankButton | MIDIMix.SoloButton
    ) -> None:
        if isinstance(event, MIDIMix.Fader):
            self._on_fader_event(event)
        elif isinstance(event, MIDIMix.Knob):
            self._on_knob_event(event)
        elif isinstance(event, MIDIMix.MuteButton):
            self._on_mute_event(event)
        elif isinstance(event, MIDIMix.RecArmButton):
            self._on_recarm_event(event)
        elif isinstance(event, MIDIMix.BankButton):
            self._on_bank_event(event)
        elif isinstance(event, MIDIMix.SoloButton):
            self._on_solo_event(event)
        else:
            logger.warning(
                f"Unkown Event {event} on midi controller {self.name}"
            )

    def _on_fader_event(self, event) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")
        if self.page == 0 and event.fader_id in range(3):
            self.mixer.mix(
                "i",
                event.fader_id + 9,
                midi_to_soundcraft_format(event.value)
            )
        elif self.page == 0 and event.fader_id in range(3, 7):
            # TODO: implement AUX Return if needed
            return None
        elif self.page == 0 and event.fader_id == 8:
            self.mixer.master(midi_to_soundcraft_format(event.value))
        elif self.page == 1 and event.fader_id in range(3):
            self.mixer.fx_setting(
                "2",
                event.fader_id + 1,
                midi_to_soundcraft_format(event.value)
            )
        elif self.page == 1 and event.fader_id in range(3, 8):
            self.mixer.fx_setting(
                "3",
                event.fader_id - 2,
                midi_to_soundcraft_format(event.value)
            )
        elif self.page == 1 and event.fader_id == 8:
            self.tempo(60 + event.value)

    def _on_knob_event(self, event) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")

    def _on_mute_event(self, event) -> None:
        if not self.mixer or not self.mixer.connected:
            logger.warning(f"controller {self.name}: Mixer not connected")
        if not event.state:
            return None
        if self.page == 0 and event.button_id in range(3):
            # (un)mute channel
            channel = event.button_id + 9
            self.mixer.mute(
                "i",
                channel,
                int(not self.mixer_config["channels"][channel]["mute"])
            )

    def _on_recarm_event(self, event) -> None:
        # TODO: figure out what to do with this buttons
        # There is no need for them right now
        pass

    def _on_bank_event(self, event) -> None:
        # Sets Knob page between 0 - 7 and 8 - 11
        if not event.state:
            return None
        if event.button_id == 1 and self.knob_page == 1:
            self.knob_page = 0
        elif event.button_id == 0 and self.knob_page == 0:
            self.knob_page = 1

    def _on_solo_event(self, event) -> None:
        # We use this as shift button
        self.shift = event.state

    def channel_update(self, msg: dict) -> None:
        if int(msg["channel"]) not in range(8, 12):
            # Channel is not on midimix
            return None
        if msg["param"] not in self.mixer_config["channels"][str(msg["channel"])]:  # noqa: E501
            # parameter is not used on midimix
            return None
        self.mixer_config["channels"][str(msg["channel"])][msg["param"]] = \
            msg["value"]

    def fx_update(self, msg: dict) -> None:
        if int(msg["fx"]) not in [2, 3]:
            # Other fx not on midimix
            return None
        if msg["param"] not in self.mixer_config["fx"][str(msg["fx"])]:
            # Ignore all params expect for skel created ones
            return None
        self.mixer_config["fx"][str(msg["fx"])][msg["param"]] = msg["value"]

    def channel_fx_update(self, msg: dict) -> None:
        self.mixer_config["channel_fx"][msg["channel"]][msg["fx"]][msg["param"]] = msg["value"]  # noqa: E501

    def master_update(self, msg: dict) -> None:
        self.mixer_config["master"] = msg["value"]

    def bpm_update(self, msg: str | int) -> None:
        self.mixer_config["bpm"] = int(msg)

    def handle_midi_com(self, msg: dict) -> None:
        if "kind" in msg and msg["kind"] == "page":
            self.page = msg["page"]

    def _request_page_update(self) -> None:
        self.mqtt.send_midi_com_message({
            "kind": "page",
            "page": "request"
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
            "master": None,
            "bpm": None,
            "fx": {
                "2": {
                    "par1": None,
                    "par2": None,
                    "par3": None,
                },
                "3": {
                    "par1": None,
                    "par2": None,
                    "par3": None,
                    "par4": None,
                    "Par5": None
                }
            },
            "channel_fx": {}
        }
        for channel in range(8, 12):
            config["channels"][str(channel)] = {
                "mix": None,
                "mute": None,
                "gain": None
            }
        for channel in range(12):
            config["channel_fx"][channel] = {}
            for fx in range(4):
                config["channel_fx"][channel][fx] = {
                    "mute": None,
                    "value": None
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
