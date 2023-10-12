import asyncio
import struct

from os import urandom

from Crypto.Cipher import AES

from bleak import BleakScanner
from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

PAIR_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1914'
COMMAND_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1912'
STATUS_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1911'
OTA_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1913'
SERV_CHAR_UUID = '00010203-0405-0607-0809-0a0b0c0d1913'

C_POWER = 0xd0

from Crypto.Cipher import AES

def notification_handler(characteristic: BleakGATTCharacteristic , data: bytearray):
    """Simple notification handler which prints the data received."""
    print("notification :: ", characteristic.description, " :: ", data)

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
        #self.btdevice = btle.Peripheral ()
        self.session_key = None
        self.command_char = None
        mesh_name = mesh_name.encode ()
        mesh_password = mesh_password.encode ()

        # Light status
        self.white_brightness = None
        self.white_temp = None
        self.color_brightness = None
        self.red = None
        self.green = None
        self.blue = None
        self.mode = None
        self.status = None

    @staticmethod
    def encrypt (key, value):
        #print("key :: ", key, " :: ", len(key))
        #print("value :: ", value, " :: ", len(value))
        assert (len(key) == 16)
        k = bytearray (key)
        val = bytearray(value.ljust (16, b'\x00'))
        #print("k :: ", len(k), " :: ",k  )
        #print("val :: ", len(val), " :: ",val  )
        k.reverse ()
        val.reverse ()
        #print("k :: ", len(k), " :: ",k  )
        #print("val :: ", len(val), " :: ",val  )
        cipher = AES.new(bytes(k), AES.MODE_ECB)
        #print("cipher :: ", k)
        
        val = bytearray(cipher.encrypt(bytes(val)))
        #print("val :: ", len(val), " :: ",val  )
        val.reverse ()

        return val

    
    @staticmethod
    def make_checksum (key, nonce, payload):
        """
        Args :
            key: Encryption key, 16 bytes
            nonce:
            payload: The unencrypted payload.
        """
        base = nonce + bytearray ([len(payload)])
        base = base.ljust (16, b'\x00')
        check =  AwoxMeshLight.encrypt (key, base)

        for i in range (0, len (payload), 16):
            check_payload = bytearray (payload[i:i+16].ljust (16, b'\x00'))
            check = bytearray([ a ^ b for (a,b) in zip(check, check_payload) ])
            check =  AwoxMeshLight.encrypt (key, check)

        return check
    

    @staticmethod
    def make_session_key (mesh_name, mesh_password, session_random, response_random):
        random = session_random + response_random
        m_n = bytearray (mesh_name.ljust (16, b'\x00'))
        m_p = bytearray (mesh_password.ljust (16, b'\x00'))
        name_pass = bytearray([ a ^ b for (a,b) in zip(m_n, m_p) ])
        key = AwoxMeshLight.encrypt (name_pass, random)
        print("key :: ", key)
        return key

    @staticmethod
    def crypt_payload (key, nonce, payload):
        """
        Used for both encrypting and decrypting.

        """
        base = bytearray(b'\x00' + nonce)
        base = base.ljust (16, b'\x00')
        result = bytearray ()

        for i in range (0, len (payload), 16):
            enc_base = AwoxMeshLight.encrypt (key, base)
            result += bytearray ([ a ^ b for (a,b) in zip (enc_base, bytearray (payload[i:i+16]))])
            base[0] += 1

        return result


    @staticmethod
    def make_command_packet (key, address, dest_id, command, data):
        """
        Args :
            key: The encryption key, 16 bytes.
            address: The mac address as a string.
            dest_id: The mesh id of the command destination as a number.
            command: The command as a number.
            data: The parameters for the command as bytes.
        """
        # Sequence number, just need to be different, idea from https://github.com/nkaminski/csrmesh
        s  = urandom (3)

        # Build nonce
        print("key :: ", key)
        print("address :: ", address)
        print("dest_id :: ", dest_id)
        print("command :: ", command)
        print("data :: ", data)
        a = bytearray.fromhex(address.replace (":",""))
        #print("a :: ", a)
        a.reverse()
        #print("a :: ", a)
        nonce = bytes(a[0:4] + b'\x01' + s)

        # Build payload
        dest = struct.pack ("<H", dest_id)
        payload = (dest + struct.pack('B', command) + b'\x60\x01' + data).ljust(15, b'\x00')

        # Compute checksum
        check = AwoxMeshLight.make_checksum (key, nonce, payload)

        # Encrypt payload
        payload = AwoxMeshLight.crypt_payload (key, nonce, payload)

        #print("payload :: ", payload)
        #print("check :: ", check)
        #print("s :: ", s)
        # Make packet
        packet = s + check[0:2] + payload
        #print("packet :: ", packet)
        return packet
    
    @staticmethod
    def make_pair_packet (mesh_name, mesh_password, session_random):
        m_n = bytearray (mesh_name.ljust (16, b'\x00'))
        m_p = bytearray (mesh_password.ljust (16, b'\x00'))
        s_r = session_random.ljust (16, b'\x00')
        name_pass = bytearray ([ a ^ b for (a,b) in zip(m_n, m_p) ])
        enc = AwoxMeshLight.encrypt (s_r ,name_pass)
        packet = bytearray(b'\x0c' + session_random) # 8bytes session_random
        packet += enc[0:8]
        return packet

    

    @staticmethod
    async def connect_to_device( mac_address):
        print("Connecting to device: {0}".format(mac_address))
        async with BleakClient(mac_address,timeout=20) as client:
            if client.is_connected:
                print("Connected: ",client.address)
    
               #self.btdevice.getCharacteristics (uuid = PAIR_CHAR_UUID)[0]

                #try:
                 #   pair_res = await client.pair(31617080)
                  #  print("Pairing...", pair_res)
                #except Exception as e:
                 #   print("Pairing failed: {0}".format(e))
                debug = False
                if debug==True:
                           
                    main_service = await client.get_services()
                    print("Main service: {0}".format(main_service))
                    for x in main_service:
                        print("*********** service: {0}".format(x.uuid))
                        main_serv = client.services.get_service(x.uuid)
                        main_char = main_serv.characteristics
                        for x in main_char:
                            print("char :: ", x)
                            test = await client.read_gatt_char(x.uuid)
                            print("data :: {0}".format(test))
              
                
                
                pair_char = await client.read_gatt_char(PAIR_CHAR_UUID)
                print("Pair characteristic data : {0}".format(pair_char) , " :: ", pair_char)


                #name = "F8GwIEDa"
                print ("client :: ", client)
                name = 'F8GwIEDa'
                key = "31617080"
                 # Converter as strings em objetos bytearray
                name = name.encode()
                key = key.encode()
                          
                # Gerar um número aleatório de 8 bytes
                session_random =  urandom(8)
            
               
               
                print("Name: ", name)
                print("Key: ", key)
                print("Session random: ")
                print(session_random)

                # Chamar a função make_pair_packet
                packet = AwoxMeshLight.make_pair_packet(name, key, session_random)

                print("packet created: {0}".format(packet))
                resp = await client.write_gatt_char(PAIR_CHAR_UUID, packet,response=True)
                print("Pair response: {0}".format(resp))

                status_char = await client.read_gatt_char(STATUS_CHAR_UUID)
                print("Status characteristic: {0}".format(status_char))
                resp = await client.write_gatt_char (STATUS_CHAR_UUID,b'\x01',response=True)
                print("Status response: {0}".format(resp))

                
           
                pair_char = await client.read_gatt_char(PAIR_CHAR_UUID)
                print("Pair resp data: ",pair_char[0])

                if pair_char[0] == 0xd :
                    session_key = AwoxMeshLight.make_session_key (name, key, session_random, pair_char[1:9])
                    print("Sending command...", len(session_key))
                    print ("Session key : %s", repr (session_key))
                    print ("Connected.")

                    #delay 5 seconds
                    await asyncio.sleep(2.0)

                    await AwoxMeshLight.writeCommand (C_POWER, b'\x00',session_key,client)
                    await client.disconnect ()
                    #packet = AwoxMeshLight.make_command_packet (session_key, "A4:C1:38:64:4B:2F", 0, 208, b"\x01")
                    #print("packet created: ",packet)
                    #cmd_char =  await client.write_gatt_char(COMMAND_CHAR_UUID,packet,True )
                    #print("cmd resp data: {0}".format(cmd_char))
                else :
                    if pair_char[0] == 0xe :
                        print ("Auth error : check name and password.")
                    else :
                        print ("Unexpected pair value : %s", repr (pair_char))
                    await client.disconnect ()
                    return False


    async def writeCommand (command, data,session_key,client ,dest = None):
        """
        Args:
            command: The command, as a number.
            data: The parameters for the command, as bytes.
            dest: The destination mesh id, as a number. If None, this lightbulb's
                mesh id will be used.
        """
        assert (session_key)
        
        #def make_command_packet (key, address, dest_id, command, data):
        packet = AwoxMeshLight.make_command_packet (session_key, client.address, 0, command, data)

        print("packet created: ",packet)

        read = await client.read_gatt_char(COMMAND_CHAR_UUID)
        print("read: ",read)

        resp = await client.write_gatt_char(COMMAND_CHAR_UUID, packet, True)
        print("cmd resp data: ",resp)

        readresp = await client.read_gatt_char(COMMAND_CHAR_UUID)
        print("read resp: ",readresp)

        

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
    else:
        ask = int(ask) - 1
        await AwoxMeshLight.connect_to_device(devices[ask])



asyncio.run(main())


#packet created: self
#b'\x0c\xcf\x8a:\xc5\x1aW\xaa\xbc>\xc3\xb5l\xf2\xf0^\xa2'
#b'\x0c[\x8d\x85\x1f\xbb:\x91\xec\x01\xa0\x03:/\xc5\x9f\x98'
#root
#b"\x0c\xb0+\x0c\xc2\x87P\x85\xc8O3a]\xdc\'\xe0\xb5"