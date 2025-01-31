from __future__ import unicode_literals

from . import packetutils as pckt

from os import urandom
#from bluepy import btle

import logging
import struct
import time


from bleak import BleakScanner
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

# Commands :

#: Set mesh groups.
#: Data : 3 bytes  
C_MESH_GROUP = 0xd7

#: Set the mesh id. The light will still answer to the 0 mesh id. Calling the 
#: command again replaces the previous mesh id.
#: Data : the new mesh id, 2 bytes in little endian order
C_MESH_ADDRESS = 0xe0

#:
C_MESH_RESET = 0xe3

#: On/Off command. Data : one byte 0, 1
C_POWER = 0xd0

#: Data : one byte
C_LIGHT_MODE = 0x33

#: Data : one byte 0 to 6 
C_PRESET = 0xc8

#: White temperature. one byte 0 to 0x7f
C_WHITE_TEMPERATURE = 0xf0

#: one byte 1 to 0x7f 
C_WHITE_BRIGHTNESS = 0xf1

#: 4 bytes : 0x4 red green blue
C_COLOR = 0xe2

#: one byte : 0xa to 0x64 .... 
C_COLOR_BRIGHTNESS = 0xf2 

#: Data 4 bytes : How long a color is displayed in a sequence in milliseconds as 
#:   an integer in little endian order
C_SEQUENCE_COLOR_DURATION = 0xf5 

#: Data 4 bytes : Duration of the fading between colors in a sequence, in 
#:   milliseconds, as an integer in little endian order
C_SEQUENCE_FADE_DURATION = 0xf6 

#: 7 bytes
C_TIME = 0xe4

#: 10 bytes
C_ALARMS = 0xe5


PAIR_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1914'
COMMAND_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1912'
STATUS_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1911'
OTA_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1913'


logger = logging.getLogger (__name__)

def notification_handler(characteristic: BleakGATTCharacteristic, data: bytearray):
    """Simple notification handler which prints the data received."""
    logger.info("RECEIVED INFO ::: %s: %r", characteristic.description, data)



class Delegate(BleakClient):
    def __init__(self, light):
        self.light = light
        #btle.DefaultDelegate.__init__(self)
        #BleakGATTCharacteristic.__init__(self)
       
    


    def handleNotification(self, cHandle, data):
        print("handleNotification")
        char = self.light.btdevice.getCharacteristics (cHandle)[0]
        if char.uuid == STATUS_CHAR_UUID:
            logger.info ("Notification on status char.")
            message = pckt.decrypt_packet (self.light.session_key, self.light.mac, data)
        else :
            logger.info ("Receiced notification from characteristic %s", char.uuid.getCommonName ())
            message = pckt.decrypt_packet (self.light.session_key, self.light.mac, data)
            logger.info ("Received message : %s", repr (message))
            self.light.parseStatusResult(message)
            self.light.message = message

class AwoxMeshLight:
    def __init__ (self, mac, mesh_name = "unpaired", mesh_password = "1234"):
        """
        Args :
            mac: The light's MAC address as a string in the form AA:BB:CC:DD:EE:FF
            mesh_name: The mesh name as a string.
            mesh_password: The mesh password as a string.
        """
        self.mac = mac
        self.mesh_id = 0
        self.btdevice = BleakClient(mac)
        self.session_key = None
        self.command_char = None
        self.mesh_name = mesh_name.encode ()
        self.mesh_password = mesh_password.encode ()

        # Light status
        self.white_brightness = None
        self.white_temp = None
        self.color_brightness = None
        self.red = None
        self.green = None
        self.blue = None
        self.mode = None
        self.status = None
        self.message = None

    async def connect(self, mesh_name = None, mesh_password = None):
        """
        Args :
            mesh_name: The mesh name as a string.
            mesh_password: The mesh password as a string.
        """
        if mesh_name : self.mesh_name = mesh_name.encode ()
        if mesh_password : self.mesh_password = mesh_password.encode ()

        print("mesh_name: ", self.mesh_name)
        print("mesh_password: ", self.mesh_password)

        assert len(self.mesh_name) <= 16, "mesh_name can hold max 16 bytes"
        assert len(self.mesh_password) <= 16, "mesh_password can hold max 16 bytes"

        await self.btdevice.connect (timeout=20.0)
        
        
        #pair_char = self.btdevice.get_services (uuid = PAIR_CHAR_UUID)[0]

        self.session_random = urandom(8)
        print("mesh_name: ", self.mesh_name)
        print("mesh_password: ", self.mesh_password)
        print("session_random: ", self.session_random)
        message = pckt.make_pair_packet (self.mesh_name, self.mesh_password, self.session_random)
        print("message: ", message)
        pair_resp = await self.btdevice.write_gatt_char(PAIR_CHAR_UUID, message, True)
        print("pair_resp: ", pair_resp)
        status_char = await self.btdevice.read_gatt_char(STATUS_CHAR_UUID)
        #status_char.write (b'\x01')
        print("status_char: ", status_char)
        status_resp = await  self.btdevice.write_gatt_char(STATUS_CHAR_UUID, b'\x01', True)
        print("status_resp: ", status_resp)


        reply = await self.btdevice.read_gatt_char (PAIR_CHAR_UUID)
        print("reply: ", reply[0])
        if reply[0] == 0xd :
            self.session_key = pckt.make_session_key (self.mesh_name, self.mesh_password, \
                self.session_random, reply[1:9])
            logger.info ("Session key : %s", repr (self.session_key))
            logger.info ("Connected.")

            services = self.btdevice.services
            for service in services:
                        print(f"[Service] {service.uuid}: (Handle: {service.handle})")
                        for char in service.characteristics:
                            print(f"\t[Characteristic] {char.uuid}: ({','.join(char.properties)}) | Name: {char.description}")
                            if "read" in char.properties:
                                if (char.uuid == STATUS_CHAR_UUID):
                                    status_char = char
                                    print("Reading...\n")
                                    try:
                                        value = bytes(await self.btdevice.read_gatt_char(char))
                                        print("value: ", value)
                                        tst2 = await self.btdevice.start_notify (char, notification_handler)
                                        print("tst2: ", tst2)
                                       
                                    except Exception as e:
                                        value = str(e).encode()
                                    else:
                                        value = "No Value"
                                    print(
                                        f"\t[Characteristic] {char.uuid}: ({','.join(char.properties)}) | Name: {char.description}, Value: {value} ")
                                    for descriptor in char.descriptors:
                                        value = await self.btdevice.read_gatt_descriptor(descriptor.handle)
                                        print(f"\t\t[Descriptor] {descriptor.uuid}: (Handle: {descriptor.handle}) | Value: {bytes(value)} ")


            #char = self.light.btdevice.getCharacteristics (cHandle)[0]
  

            return True
        else :
            if reply[0] == 0xe :
                logger.info ("Auth error : check name and password.")
            else :
                logger.info ("Unexpected pair value : %s", repr (reply))
            await self.disconnect ()
            return False

    def connectWithRetry(self, num_tries = 1, mesh_name = None, mesh_password = None):
        """
        Args:
           num_tries: The number of attempts to connect.
           mesh_name: The mesh name as a string.
           mesh_password: The mesh password as a string.
        """
        connected = False
        attempts = 0
        while (not connected and attempts < num_tries ):
            try:
                connected = self.connect(mesh_name, mesh_password)
            except Exception as e:
                logger.info("connection_error: retrying for %s time", attempts , e)
            finally:
                attempts += 1

        return connected

    def setMesh (self, new_mesh_name, new_mesh_password, new_mesh_long_term_key):
        """
        Sets or changes the mesh network settings.

        Args :
            new_mesh_name: The new mesh name as a string, 16 bytes max.
            new_mesh_password: The new mesh password as a string, 16 bytes max.
            new_mesh_long_term_key: The new long term key as a string, 16 bytes max.

        Returns :
            True on success.
        """
        assert (self.session_key), "Not connected"
        assert len(new_mesh_name.encode()) <= 16, "new_mesh_name can hold max 16 bytes"
        assert len(new_mesh_password.encode()) <= 16, "new_mesh_password can hold max 16 bytes"
        assert len(new_mesh_long_term_key.encode()) <= 16, "new_mesh_long_term_key can hold max 16 bytes"

        pair_char = self.btdevice.getCharacteristics (uuid = PAIR_CHAR_UUID)[0]

        # FIXME : Removing the delegate as a workaround to a bluepy.btle.BTLEException
        #         similar to https://github.com/IanHarvey/bluepy/issues/182 That may be
        #         a bluepy bug or I'm using it wrong or both ...
        self.btdevice.setDelegate (None)

        message = pckt.encrypt (self.session_key, new_mesh_name.encode ())
        message.insert (0, 0x4)
        pair_char.write (message)

        message = pckt.encrypt (self.session_key, new_mesh_password.encode ())
        message.insert (0, 0x5)
        pair_char.write (message)

        message = pckt.encrypt (self.session_key, new_mesh_long_term_key.encode ())
        message.insert (0, 0x6)
        pair_char.write (message)

        time.sleep (1)
        reply = bytearray (pair_char.read ())

        self.btdevice.setDelegate (Delegate (self))

        if reply[0] == 0x7 :
            self.mesh_name = new_mesh_name.encode ()
            self.mesh_password = new_mesh_password.encode ()
            logger.info ("Mesh network settings accepted.")
            return True
        else:
            logger.info ("Mesh network settings change failed : %s", repr(reply))
            return False

    def setMeshId (self, mesh_id):
        """
        Sets the mesh id.

        Args :
            mesh_id: as a number.

        """
        data = struct.pack ("<H", mesh_id)
        self.writeCommand (C_MESH_ADDRESS, data)
        self.mesh_id = mesh_id

    async def writeCommand (self, command, data, dest = None):
        print("writeCommand")
        """
        Args:
            command: The command, as a number.
            data: The parameters for the command, as bytes.
            dest: The destination mesh id, as a number. If None, this lightbulb's
                mesh id will be used.
        """
        assert (self.session_key)
        if dest == None: dest = self.mesh_id
        packet = pckt.make_command_packet (self.session_key, self.mac, dest, command, data)

        if not self.command_char:
            #self.command_char = self.btdevice.getCharacteristics (uuid=COMMAND_CHAR_UUID)[0]
            self.command_char = await self.btdevice.read_gatt_char(COMMAND_CHAR_UUID)
            print("self.command_char: ", self.command_char)

        try:
            logger.info ("[%s] Writing command %i data %s", self.mac, command, repr (data))
            #self.command_char.write(packet)
            print("packet: ", packet)
            await self.btdevice.write_gatt_char(COMMAND_CHAR_UUID, packet, True)
        except:
            logger.info('[%s] (Re)load characteristics', self.mac)
            #self.command_char = self.btdevice.getCharacteristics(uuid=COMMAND_CHAR_UUID)[0]
            self.command_char = await  self.btdevice.read_gatt_char(COMMAND_CHAR_UUID)
            logger.info ("[%s] Writing command %i data %s", self.mac, command, repr (data))
            print("except packet: ", packet)
            #self.command_char.write(packet)
            await self.btdevice.write_gatt_char(COMMAND_CHAR_UUID, packet, True)

    def resetMesh (self):
        """
        Restores the default name and password. Will disconnect the device.
        """
        self.writeCommand (C_MESH_RESET, b'\x00')

    def readStatus (self):
        print("readStatus")
        status_char = self.btdevice.getCharacteristics (uuid = STATUS_CHAR_UUID)[0]
        packet = status_char.read ()
        return pckt.decrypt_packet (self.session_key, self.mac, packet)

    def parseStatusResult(self, message):
        print("parseStatusResult")
        meshid = struct.unpack('B', message[3:4])[0]
        mode = struct.unpack('B', message[12:13])[0]

        if mode < 40 and meshid == 0:  # filter some messages that return something else
            # mode 1 = white
            # mode 5 = white
            # mode 3 = color
            # mode 7 = transition
            self.mode = mode
            self.status = mode % 2

            self.white_brightness, self.white_temp = struct.unpack('BB', message[13:15])
            self.color_brightness, self.red, self.green, self.blue = struct.unpack('BBBB', message[15:19])

    def setColor (self, red, green, blue):
        """
        Args :
            red, green, blue: between 0 and 0xff
        """
        data = struct.pack ('BBBB', 0x04, red, green, blue)
        self.writeCommand (C_COLOR, data)

    def setColorBrightness (self, brightness):
        """
        Args :
            brightness: a value between 0xa and 0x64 ...
        """
        data = struct.pack ('B', brightness)
        self.writeCommand (C_COLOR_BRIGHTNESS, data)

    def setSequenceColorDuration (self, duration):
        """
        Args :
            duration: in milliseconds.
        """
        data = struct.pack ("<I", duration)
        self.writeCommand (C_SEQUENCE_COLOR_DURATION, data)

    def setSequenceFadeDuration (self, duration):
        """
        Args:
            duration: in milliseconds.
        """
        data = struct.pack ("<I", duration)
        self.writeCommand (C_SEQUENCE_FADE_DURATION, data)

    def setPreset (self, num):
        """
        Set a preset color sequence.

        Args :
            num: number between 0 and 6
        """
        data = struct.pack('B', num)
        self.writeCommand (C_PRESET, data)

    def setWhiteBrightness(self, brightness):
        """
        Args :
            brightness: between 1 and 0x7f
        """
        data = struct.pack('B', brightness)
        self.writeCommand(C_WHITE_BRIGHTNESS, data)

    def setWhiteTemperature(self, brightness):
        """
        Args :
            temp: between 0 and 0x7f
        """
        data = struct.pack('B', brightness)
        self.writeCommand(C_WHITE_TEMPERATURE, data)

    async def setWhite (self, temp, brightness):
        """
        Args :
            temp: between 0 and 0x7f
            brightness: between 1 and 0x7f
        """
        data = struct.pack ('B', temp)
        await self.writeCommand (C_WHITE_TEMPERATURE, data)
        data = struct.pack ('B', brightness)
        await self.writeCommand (C_WHITE_BRIGHTNESS, data)

    async def on (self):
        """ Turns the light on.
        """
        await self.writeCommand (C_POWER, b'\x01')

    async def off (self):
        """ Turns the light off.
        """
        await self.writeCommand (C_POWER, b'\x00')

    async def disconnect (self):
        logger.info ("Disconnecting.")
        state = await self.btdevice.disconnect ()
        logger.info ("Disconnected.")
        self.session_key = None

    async def getFirmwareRevision (self):
        """
        Returns :
            The firmware version as a null terminated utf-8 string.
        """
        char = await self.btdevice.read_gatt_char("00002a26-0000-1000-8000-00805f9b34fb")
        return char

    async def getHardwareRevision (self):
        """
        Returns :
            The hardware version as a null terminated utf-8 string.
        """
        char = await self.btdevice.read_gatt_char("00002a27-0000-1000-8000-00805f9b34fb")
        return char

    async def getModelNumber (self):
        """
        Returns :
            The model as a null terminated utf-8 string.
        """
        #char = self.btdevice.getCharacteristics (uuid=btle.AssignedNumbers.modelNumberString)[0]
        char = await self.btdevice.read_gatt_char("00002a24-0000-1000-8000-00805f9b34fb")
        return char

#**********************************************************

    async def sendFirmware (self, firmware_path):
        """
        Updates the light bulb's firmware. The light will blink green after receiving the new
        firmware.

        Args:
            firmware_path: The path of the firmware file.
        """
        assert (self.session_key)

        with open (firmware_path, 'rb') as firmware_file :
            firmware_data = firmware_file.read()

        if not firmware_data :
            return

        ota_char = self.btdevice.getCharacteristics (uuid=OTA_CHAR_UUID)[0]
        count = 0
        for i in range (0, len (firmware_data), 0x10):
            data = struct.pack ('<H', count) + firmware_data [i:i+0x10].ljust (0x10, b'\xff')
            crc = pckt.crc16 (data)
            packet = data + struct.pack ('<H', crc)
            logger.debug ("Writing packet %i of %i : %s", count + 1, len(firmware_data)/0x10 + 1, repr(packet))
            ota_char.write (packet)
            # FIXME : When calling write with withResponse=True bluepy hangs after a few packets.
            #         Without any delay the light blinks once without accepting the firmware.
            #         The choosen value is arbitrary.
            time.sleep (0.01)
            count += 1
        data = struct.pack ('<H', count)
        crc = pckt.crc16 (data)
        packet = data + struct.pack ('<H', crc)
        logger.debug ("Writing last packet : %s", repr(packet))
        ota_char.write (packet)
