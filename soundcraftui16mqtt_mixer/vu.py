from base64 import b64decode
from json import loads, dumps

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
                            "post": vu_values[index+1],
                            "fader": vu_values[index+2]
                        },
                        "gain": {
                            "pre": vu_values[index+3],
                            "post": vu_values[index+4]
                        }
                    }
                    index += 6
                elif channel_type in ["aux", "master"]:
                    self.data[channel_type][f"{block}"] = {
                        "mix": {
                            "post": vu_values[index],
                            "fader": vu_values[index+1]
                        },
                        "master": {
                            "post": vu_values[index+2],
                            "fader": vu_values[index+3]
                        }
                    }
                    index += 5
                elif channel_type in ["fx", "sub"]:
                    self.data[channel_type][f"{block}"] = {
                        "mix": {
                            "post_left": vu_values[index],
                            "post_right": vu_values[index+1],
                            "fader_left": vu_values[index+2],
                            "fader_right": vu_values[index+3]
                        },
                        "master": {
                            "fader_left": vu_values[index+4],
                            "fader_right": vu_values[index+5]
                        }
                    }
                    index += 7

    def format_from_mqtt(self, json: str) -> None:
        self.data = loads(json)

    def get_as_mqtt(self) -> None:
        return dumps(self.data)
