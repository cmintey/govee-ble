def decode_temp(packet_value: int) -> float:
    """
    https://github.com/Home-Is-Where-You-Hang-Your-Hack/sensor.goveetemp_bt_hci/blob/master/custom_components/govee_ble_hci/govee_advertisement.py
    """
    if packet_value & 0x800000:
        return float((packet_value ^ 0x800000) / -10000)
    return float(packet_value / 10000)


def decode_humidity(packet_value: int) -> float:
    return float((packet_value % 1000) / 10)


def c_to_f(c: float) -> float:
    return (c * 9 / 5) + 32
