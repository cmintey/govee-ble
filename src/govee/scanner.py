from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from govee.advertisement import process_advertisement


class GoveeScanner:
    def __init__(self, addresses=[]):
        self._callbacks = []
        self.addresses = addresses
        self.scanner = None

    def register(self, callback):
        self._callbacks.append(callback)

    def unregister(self, callback):
        self._callbacks.remove(callback)

    async def start(self):
        def _callback(device: BLEDevice, adv: AdvertisementData):
            if device.address in self.addresses:
                adv = process_advertisement(device, adv)
                if adv:
                    for callback in self._callbacks:
                        callback(adv.dict())
        self.scanner = BleakScanner()
        self.scanner.register_detection_callback(_callback)
        await self.scanner.start()

    async def stop(self):
        await self.scanner.stop()
