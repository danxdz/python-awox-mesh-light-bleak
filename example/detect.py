#!/usr/bin/env python3
# -*- mode: python; python-indent-offset: 4; indent-tabs-mode: nil -*-
# SPDX-License-Indentifier: MIT

''' Example '''

import asyncio
import os
import sys

PARENT_PATH = os.path.join(__file__, '..', '..', 'awoxmeshlight', '..')
LIB_PATH = os.path.abspath(PARENT_PATH)
sys.path.append(LIB_PATH)

from awoxmeshlight import AwoxMeshLight

async def main():

    MAC = os.getenv('MAC') or "A4:C1:38:77:2A:18"
    print("info: Looking up mac=%s" % MAC)
    LIGHT = AwoxMeshLight(MAC,"F8GwIEDa","31617080")
    await LIGHT.connect()
    print("info: model=%s" % await LIGHT.getModelNumber())
    print("info: hardware=%s" % await LIGHT.getHardwareRevision())
    print("info: firmware=%s" % await LIGHT.getFirmwareRevision())
    await LIGHT.disconnect()


asyncio.run(main())