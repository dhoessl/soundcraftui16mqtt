from scipy.interpolate import interp1d
from math import floor


def power_format(val: float, min: int, max: int) -> float:
    return min * ((max/min) ** float(val))


def percent_format(val: float, min: int, max: int) -> float:
    return interp1d([0, 1], [min, max])(float(val))


def delay_time_format(val: float) -> float:
    return interp1d(
        [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        [100, 154, 229, 323, 435, 562, 691, 812, 912, 977, 1000],
        kind="linear",
        fill_value="extrapolate"
    )(float(val))


def room_time_format(val: float) -> float:
    return 100 * (10 ** float(val))


def mix_format(val: float) -> float:
    if float(val) == 0:
        return -99
    if float(val) <= 0.527044025:
        return -100 + 110 * (float(val) ** 0.32)
    else:
        return interp1d([0.527044025, 1], [-10, 10])(float(val))


def midi_to_soundcraft_format(val: int) -> float:
    return int(val) / 127


def soundcraft_to_midi_format(val: float) -> int:
    return floor(interp1d([0, 1], [0, 127])(float(val)))


def midi_grid_to_soundcraft_format(val: int) -> float:
    return int(val) / 8


def soundcraft_to_midi_grid_format(val: float) -> int:
    return floor(interp1d([0, 1], [0, 8])(float(val)))
