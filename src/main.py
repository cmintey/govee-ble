import asyncio
import yaml
import json
import paho.mqtt.client as mqtt
import logging
import logging.config

from govee.scanner import GoveeScanner

logging.config.fileConfig('./src/logger.conf')
logger = logging.getLogger("main")


def get_config() -> dict:
    config = {}
    logger.info("getting config...")
    with open("/config/config.yml") as f:
        config = yaml.load(f, yaml.SafeLoader)
    return config


def get_topic(name: str, prefix: str = "govee") -> str:
    return f"{prefix}/sensor/{name.replace(' ', '_').lower()}"


def save_device(address: str, is_configured: bool = True) -> None:
    logger.info("saving device...")
    config = get_config()
    device: dict = config.get('devices').get(address)
    device['configured'] = is_configured

    config['devices'][address] = device
    with open("./config/config.yml", "w") as f:
        config = yaml.dump(config, f)


def initialize(config: dict, data: dict) -> None:
    logger.info("initializing")
    address: str = data['address']
    name: str = config['devices'][address]['name']
    state_topic: str = f"{get_topic(name)}/state"

    device: dict = {
        "identifiers": [
            f"govee_{address.replace(':', '')}"
        ],
        "manufacturer": "Govee",
        "model": "H5075",
        "name": f"{name} Hygrometer / Thermometer"
    }

    battery_payload: dict = {
        "device_class": "battery",
        "name": f"{name} Battery",
        "unit_of_measurement": "%",
        "value_template": "{{ value_json.battery }}",
        "state_topic": state_topic,
        "device": device,
        "entity_category": "diagnostic",
        "unique_id": f"{address.replace(':', '')}_battery_govee"
    }
    temperature_payload: dict = {
        "device_class": "temperature",
        "name": f"{name} Temperature",
        "unit_of_measurement": "°F",
        "value_template": "{{ value_json.temperature | round(1) }}",
        "state_topic": state_topic,
        "state_class": "measurement",
        "device": device,
        "unique_id": f"{address.replace(':', '')}_temperature_govee"
    }
    humidity_payload: dict = {
        "device_class": "humidity",
        "name": f"{name} Humidity",
        "unit_of_measurement": "%",
        "value_template": "{{ value_json.humidity }}",
        "state_topic": state_topic,
        "state_class": "measurement",
        "device": device,
        "unique_id": f"{address.replace(':', '')}_humidity_govee"
    }

    discovery_topic: str = get_topic(name, 'homeassistant')

    client = mqtt.Client()
    client.connect(config['mqtt']['broker'])
    client.publish(f"{discovery_topic}/battery/config",
                   json.dumps(battery_payload), 0, True)
    client.publish(f"{discovery_topic}/temperature/config",
                   json.dumps(temperature_payload), 0, True)
    client.publish(f"{discovery_topic}/humidity/config",
                   json.dumps(humidity_payload), 0, True)
    client.disconnect()

    save_device(address, True)


def remove_device(config: dict, data: dict) -> None:
    address: str = data['address']
    name: str = config['devices'][address]['name']
    discovery_topic: str = get_topic(name, 'homeassistant')

    client = mqtt.Client()
    client.connect(config['mqtt']['broker'])
    client.publish(f"{discovery_topic}/battery/config", '')
    client.publish(f"{discovery_topic}/temperature/config", '')
    client.publish(f"{discovery_topic}/humidity/config", '')
    client.disconnect()

    save_device(address, False)


def send_message(config: dict, data: dict):
    payload = {}
    payload['battery'] = data['battery']
    payload['humidity'] = data['humidity']
    payload['temperature'] = data['temperature']

    name = config['devices'][data['address']]['name']

    client = mqtt.Client()
    client.connect(config['mqtt']['broker'])
    client.publish(f"{get_topic(name)}/state", json.dumps(payload))
    client.disconnect()
    logger.info(f"{get_topic(name)}/state: {json.dumps(payload)}")


def is_configured(config: dict, address: str) -> bool:
    return config['devices'][address].get("configured", False)


def should_remove(config: dict, address: str) -> bool:
    return config['devices'][address].get("remove", False)


def found_device(data: dict, config: dict) -> None:
    # config = get_config()
    if config['homeassistant'] and not is_configured(config, data['address']):
        initialize(config, data)
    # if config['homeassistant'] and should_remove(config, data['address']):
    #     remove_device(config, data)
    send_message(config, data)


async def main(config: dict) -> None:
    addresses = [k for k in config['devices'].keys()]
    scanner = GoveeScanner(addresses)
    scanner.register(lambda data: found_device(data, config))
    while True:
        await scanner.start()
        logger.debug("scanning...")
        await asyncio.sleep(10.0)
        logger.debug("stopping...")
        await scanner.stop()
        logger.debug("sleeping...")
        await asyncio.sleep(10.0)


if __name__ == '__main__':
    logger.info("Starting application...")
    config = get_config()
    asyncio.run(main(config))
