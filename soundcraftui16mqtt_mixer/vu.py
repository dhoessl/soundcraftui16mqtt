from base64 import b64decode
from json import loads, dumps
from .formatting import mix_format

# This part is heavily influenced by fmelchers logic on soundcraft-ui
# implementation in NX
# Source: https://github.com/fmalcher/soundcraft-ui/tree/main


class VUData:
    def __init__(self) -> None:
        self.factor = 0.004167508166392142
        self.order = [
            "input", "player", "sub", "fx", "aux", "master", "line"
        ]
        self.data = {
            "input": {},
            "player": {},
            "sub": {},
            "fx": {},
            "aux": {},
            "master": {},
            "line": {}
        }

    def format_from_base64(self, b64_str: str) -> None:
        vu_values = list(b64decode(b64_str))
        index = 8
        for channel_type in self.order:
            for block in range(vu_values[self.order.index(channel_type)]):
                if channel_type in ["input", "player", "line"]:
                    self.data[channel_type][f"{block}"] = {
                        "mix": {
                            "pre": vu_values[index],
                            "pre_formated":
                                f"{mix_format(vu_values[index]):.1f}",
                            "post": vu_values[index+1],
                            "post_formated":
                                f"{mix_format(vu_values[index+1]):.1f}",
                            "fader": vu_values[index+2],
                            "fader_formated":
                                f"{mix_format(vu_values[index+2]):.1f}"
                        },
                        "gain": {
                            "pre": vu_values[index+3],
                            "pre_formated":
                                f"{mix_format(vu_values[index+3]):.1f}",
                            "post": vu_values[index+4],
                            "post_formated":
                                f"{mix_format(vu_values[index+4]):.1f}"
                        }
                    }
                    index += 6
                elif channel_type in ["aux", "master"]:
                    self.data[channel_type][f"{block}"] = {
                        "mix": {
                            "post": vu_values[index],
                            "post_formated":
                                f"{mix_format(vu_values[index]):.1f}",
                            "fader": vu_values[index+1],
                            "fader_formated":
                                f"{mix_format(vu_values[index+1]):.1f}"
                        },
                        "master": {
                            "post": vu_values[index+2],
                            "post_formated":
                                f"{mix_format(vu_values[index+2]):.1f}",
                            "fader": vu_values[index+3],
                            "fader_formated":
                                f"{mix_format(vu_values[index+3]):.1f}"
                        }
                    }
                    index += 5
                elif channel_type in ["fx", "sub"]:
                    self.data[channel_type][f"{block}"] = {
                        "mix": {
                            "post_left": vu_values[index],
                            "post_left_formated":
                                f"{mix_format(vu_values[index]):.1f}",
                            "post_right": vu_values[index+1],
                            "post_right_formated":
                                f"{mix_format(vu_values[index+1]):.1f}",
                            "fader_left": vu_values[index+2],
                            "fader_left_formated":
                                f"{mix_format(vu_values[index+2]):.1f}",
                            "fader_right": vu_values[index+3],
                            "fader_right_formated":
                                f"{mix_format(vu_values[index+3]):.1f}"
                        },
                        "master": {
                            "fader_left": vu_values[index+4],
                            "fader_left_formated":
                                f"{mix_format(vu_values[index+4]):.1f}",
                            "fader_right": vu_values[index+5],
                            "fader_right_formated":
                                f"{mix_format(vu_values[index+5]):.1f}"
                        }
                    }
                    index += 7

    def format_from_mqtt(self, json: str) -> None:
        self.data = loads(json)

    def get_as_mqtt(self) -> None:
        return dumps(self.data)
