from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from ble_serial.constants import ble_chars
import logging, asyncio
from typing import Optional

class BLE_interface():
    async def start(self, addr_str, addr_type, adapter, write_uuid, read_uuid,):
        self.dev = BleakClient(addr_str) # addr_type only on Windows?, adapter in kwargs
        await self.dev.connect()
        logging.info(f'Connected device {self.dev}')

        self.write_char = self.find_char(write_uuid, 'write-without-response')
        self.read_char = self.find_char(read_uuid, 'notify')

        await self.dev.start_notify(self.read_char, self.handleNotification)

    def find_char(self, uuid: Optional[str], req_prop: str) -> BleakGATTCharacteristic:
        found_char = None

        # Use user supplied UUID first, otherwise try included list
        if uuid:
            uuid_candidates = uuid
        else:
            uuid_candidates = ble_chars
            logging.debug(f'No {req_prop} uuid specified, trying {ble_chars}')

        for srv in self.dev.services:
            for c in srv.characteristics:
                if c.uuid in uuid_candidates:
                    found_char = c
                    logging.debug(f'Found {req_prop} characteristic {c}')
                    break

        # Check if it has the required properties
        assert found_char, \
            "No characteristic with specified UUID found!"
        assert (req_prop in found_char.properties), \
            f"Specified characteristic has no {req_prop} property!"

        return found_char

    def set_receiver(self, callback):
        self._cb = callback
        logging.info('Receiver set up')

    async def shutdown(self):
        await self.dev.stop_notify(self.read_char)
        await self.dev.disconnect()
        logging.info('BT disconnected')

    def send(self, data: bytes):
        logging.debug(f'Sending {data}')
        # TODO use queue instead
        asyncio.create_task(self.dev.write_gatt_char(self.write_char, data))

    def handleNotification(self, handle: int, data: bytes):
        logging.debug(f'Received notify from {handle}: {data}')
        self._cb(data)