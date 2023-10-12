import asyncio
import codecs

from bleak import exc
from bleak import BleakClient

DEVICE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_LABEL = "Device Name: "

async def run(address, num_attempts=10, debug=True):

    global result

    print('Connecting...')
    for i in range (num_attempts): # note, this for loop is to avoid the software failing connection issue
        print(f'attempt: {i}')
        try:
            print('Attempting connection')
            async with BleakClient(address) as client:
                print('Connnected')

                for service in client.services:
                    print(f"[Service] {service.uuid}: (Handle: {service.handle})")
                    for char in service.characteristics:
                        print(f"\t[Characteristic] {char.uuid}: ({','.join(char.properties)}) | Name: {char.description}")
                        if "read" in char.properties:
                            if (char.uuid == DEVICE_NAME_UUID):
                                print("Reading...\n")
                                data = await client.read_gatt_char(char.uuid)
                                print(DEVICE_NAME_LABEL,codecs.decode(data, 'UTF-8'))

                                try:
                                    value = bytes(await client.read_gatt_char(char.uuid))
                                except Exception as e:
                                    value = str(e).encode()
                                else:
                                    value = "No Value"
                                print(
                                    f"\t[Characteristic] {char.uuid}: ({','.join(char.properties)}) | Name: {char.description}, Value: {value} ")
                                for descriptor in char.descriptors:
                                    value = await client.read_gatt_descriptor(descriptor.handle)
                                    print(f"\t\t[Descriptor] {descriptor.uuid}: (Handle: {descriptor.handle}) | Value: {bytes(value)} ")

                for service in client.services:
                    for char in service.characteristics:
                        if "write" in char.properties:
                            if (char.uuid == DEVICE_NAME_UUID):
                                print('Writing...\n')
                                data = codecs.encode('TEST', 'UTF-8')
                                await client.write_gatt_char(DEVICE_NAME_UUID, data, response=False)
                                print(f'written: {data} to {DEVICE_NAME_UUID}')
            print('Written, breaking out of for loop')
            break
        except exc.BleakDBusError:
                print('\n>> Bleak ERROR: Software caused connection abort <<\n')
                continue

        if(i == (num_attempts-1)):
            print(f"No connection after {num_attempts} attempts: ABORTING program")
            quit()

    print('disconnecting')    
    await client.disconnect()
        

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    address = 'A4:C1:38:77:2A:18'

    asyncio.run(run(address))