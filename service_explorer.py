"""
Service Explorer
----------------

An example showing how to access and print out the services, characteristics and
descriptors of a connected GATT server.

Created on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

import argparse
import asyncio
import logging

from bleak import BleakClient, BleakScanner

logger = logging.getLogger(__name__)


async def main(args: argparse.Namespace):
    logger.info("starting scan...")

    if args.address:
        device = await BleakScanner.find_device_by_address(
            args.address, cb=dict(use_bdaddr=args.macos_use_bdaddr)
        )
        if device is None:
            logger.error("could not find device with address '%s'", args.address)
            return
    else:
        device = await BleakScanner.find_device_by_name(
            args.name, cb=dict(use_bdaddr=args.macos_use_bdaddr)
        )
        if device is None:
            logger.error("could not find device with name '%s'", args.name)
            return

    logger.info("connecting to device...")

    async with BleakClient(
        device,
        services=args.services,
    ) as client:
        logger.info("connected")

        for service in client.services:
            logger.info("[Service] %s", service)

            for char in service.characteristics:
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char.uuid)
                        logger.info(
                            "  [Characteristic] %s (%s), Value: %r",
                            char,
                            ",".join(char.properties),
                            value,
                        )
                    except Exception as e:
                        logger.error(
                            "  [Characteristic] %s (%s), Error: %s",
                            char,
                            ",".join(char.properties),
                            e,
                        )

                else:
                    logger.info(
                        "  [Characteristic] %s (%s)", char, ",".join(char.properties)
                    )

                for descriptor in char.descriptors:
                    try:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        logger.info("    [Descriptor] %s, Value: %r", descriptor, value)
                    except Exception as e:
                        logger.error("    [Descriptor] %s, Error: %s", descriptor, e)

        logger.info("disconnecting...")

    logger.info("disconnected")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    device_group = parser.add_mutually_exclusive_group(required=True)

    device_group.add_argument(
        "--name",
        metavar="<name>",
        help="the name of the bluetooth device to connect to",
    )
    device_group.add_argument(
        "--address",
        metavar="<address>",
        help="the address of the bluetooth device to connect to",
    )

    parser.add_argument(
        "--macos-use-bdaddr",
        action="store_true",
        help="when true use Bluetooth address instead of UUID on macOS",
    )

    parser.add_argument(
        "--services",
        nargs="+",
        metavar="<uuid>",
        help="if provided, only enumerate matching service(s)",
    )

    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="sets the log level to debug",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)-15s %(name)-8s %(levelname)s: %(message)s",
    )

    asyncio.run(main(args))




    service_explorer.py


[Service] 00001800-0000-1000-8000-00805f9b34fb (Handle: 1): Generic Access Profile
[Characteristic] 00002a00-0000-1000-8000-00805f9b34fb (Handle: 2): DevName (read), Value: bytearray(b'EFueva_225s\x00')
[Descriptor] 00002901-0000-1000-8000-00805f9b34fb (Handle: 4): Characteristic User Description, Value: bytearray(b'DevName')
[Characteristic] 00002a01-0000-1000-8000-00805f9b34fb (Handle: 5): Appearance (read), Value: bytearray(b'\x00\x00')

[Service] 0000180a-0000-1000-8000-00805f9b34fb (Handle: 7): Device Information
[Characteristic] 00002a26-0000-1000-8000-00805f9b34fb (Handle: 8): Firmware Revision String (read), Value: bytearray(b'1.3.3\x00')
[Characteristic] 00002a29-0000-1000-8000-00805f9b34fb (Handle: 10): Manufacturer Name String (read), Value: bytearray(b'AwoX\x00')
[Characteristic] 00002a24-0000-1000-8000-00805f9b34fb (Handle: 12): Model Number String (read), Value: bytearray(b'EFueva_225s\x00')
[Characteristic] 00002a27-0000-1000-8000-00805f9b34fb (Handle: 14): Hardware Revision String (read), Value: bytearray(b'1.0')

[Service] 00010203-0405-0607-0809-0a0b0c0d1910 (Handle: 16): Unknown
[Characteristic] 00010203-0405-0607-0809-0a0b0c0d1911 (Handle: 17): Status (read,write,notify), Value: bytearray(b'\x01')
[Descriptor] 00002901-0000-1000-8000-00805f9b34fb (Handle: 19): Characteristic User Description, Value: bytearray(b'Status')
[Characteristic] 00010203-0405-0607-0809-0a0b0c0d1912 (Handle: 20): Command (read,write-without-response,write), Value: bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
[Descriptor] 00002901-0000-1000-8000-00805f9b34fb (Handle: 22): Characteristic User Description, Value: bytearray(b'Command')
[Characteristic] 00010203-0405-0607-0809-0a0b0c0d1913 (Handle: 23): OTA (read,write-without-response), Value: bytearray(b'\xe0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
[Descriptor] 00002901-0000-1000-8000-00805f9b34fb (Handle: 25): Characteristic User Description, Value: bytearray(b'OTA')
[Characteristic] 00010203-0405-0607-0809-0a0b0c0d1914 (Handle: 26): Pair (read,write), Value: bytearray(b'\x00')
[Descriptor] 00002901-0000-1000-8000-00805f9b34fb (Handle: 28): Characteristic User Description, Value: bytearray(b'Pair')

