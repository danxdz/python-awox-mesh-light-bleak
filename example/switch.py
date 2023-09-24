
import asyncio
import os
import sys

PARENT_PATH = os.path.join(__file__, '..', '..', 'awoxmeshlight', '..')
LIB_PATH = os.path.abspath(PARENT_PATH)
sys.path.append(LIB_PATH)

from awoxmeshlight import AwoxMeshLight

import logging

logger = logging.getLogger("awoxmeshlight")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler ()
handler.setLevel(logging.DEBUG)
logger.addHandler (handler)



async def main():

    mylight = AwoxMeshLight ("A4:C1:38:77:2A:18", "F8GwIEDa", "31617080")
    #mylight = awoxmeshlight.AwoxMeshLight ("A4:C1:38:64:4B:2F", "F8GwIEDa", "31617080")
    print(mylight)
    await mylight.connect()

    #mylight.setColor(0xFF, 0x00, 0x00) #red
    #mylight.setColor(0x00, 0xFF, 0x00) #green
    #mylight.setColor(0x00, 0x00, 0xFF) #blue


    await mylight.setWhite(0x10, 0x40) #coldwhite

    await mylight.on()
    await mylight.off()
    await mylight.disconnect()



asyncio.run(main())