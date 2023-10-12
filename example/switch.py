
import asyncio
import os
import sys

from bleak import BleakScanner

PARENT_PATH = os.path.join(__file__, '..', '..', 'awoxmeshlight', '..')
LIB_PATH = os.path.abspath(PARENT_PATH)
sys.path.append(LIB_PATH)

from awoxmeshlight import AwoxMeshLight
import sys



import logging

logger = logging.getLogger("awoxmeshlight")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler ()
handler.setLevel(logging.DEBUG)
logger.addHandler (handler)



async def main():

    devices = await BleakScanner.discover()
    i=0
    for d in devices:
        i = i + 1
        print(i , " :: ", d)

    if len(devices) == 0:
        print("No devices found, please check your Bluetooth device settings and try again.")
        await main()
    
    print("Found {0} devices.".format(len(devices)))
   
    ask =  input("Please select your device by typing the number next to it, or 0 to restart. ")
    #convertendo para inteiro
    if int(ask) == 0:
        await main()
    elif ask == "":
        ask = 0
        await main()
    else:
        ask = int(ask) - 1
        #await AwoxMeshLight.connect_to_device(devices[ask])


    selected_device = devices[ask].address
    print("Selected device address:", selected_device)
    mylight = AwoxMeshLight(selected_device, "F8GwIEDa", "31617080")

    #mylight = AwoxMeshLight (str(devices[ask]), "F8GwIEDa", "31617080")
    #mylight = AwoxMeshLight ("A4:C1:38:77:2A:18", "F8GwIEDa", "31617080")
    
    #mylight = awoxmeshlight.AwoxMeshLight ("A4:C1:38:64:4B:2F", "F8GwIEDa", "31617080")
    print(mylight)
    await mylight.connect()

    #mylight.setColor(0xFF, 0x00, 0x00) #red
    #mylight.setColor(0x00, 0xFF, 0x00) #green
    #mylight.setColor(0x00, 0x00, 0xFF) #blue


    await mylight.setWhite(0x10, 0x40) #coldwhite

    #await mylight.on()
    await mylight.off()
    await mylight.disconnect()



asyncio.run(main())