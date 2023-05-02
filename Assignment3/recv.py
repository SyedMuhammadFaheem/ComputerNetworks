import binascii
import socket
import struct
import sys
import hashlib
import random
import time



def buildACKChecksum(valueOfSeq, data):
    values = (valueOfSeq, data)
    packer = struct.Struct('I {}s'.format(len(data)))
    packed_data = packer.pack(*values)
    return bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")


ip = "127.0.0.1"
port = 5005
#unpacker = struct.Struct('I 8s 32s')

currentACKNum = 0  
wrongACK = 1 


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
sock.bind((ip, port))

while True: 

    data, addr = sock.recvfrom(1024)  

    unpacker = struct.Struct('I {}s 32s'.format(len(data)-36))
    packet = unpacker.unpack(data)
    print("Received Message from Client: ", packet)

    

    chksum = buildACKChecksum(packet[0], packet[1])

   
    if packet[2] == chksum:

        print("Checksums Match, Packet OK")
        hold = packet[1].decode("utf-8")
        print("Data Recieved from client : ",hold)

        if packet[0] == currentACKNum:  

       
            chksumACK = buildACKChecksum(currentACKNum, b'\x00' * 8)

            
            resp_val = (currentACKNum, b"", chksumACK)
            resp_data = struct.Struct('I 8s 32s')
            rpacket = resp_data.pack(*resp_val)

            print("Sent Packet to Client: ", rpacket)
            sock.sendto(rpacket, addr)  

           
            if currentACKNum == 0:
                currentACKNum = 1
                wrongACK = 0

            elif currentACKNum == 1:
                currentACKNum = 0
                wrongACK = 1

    else:

        print("Checksums Don't Match, Packet Corrupt")

        
        chksumACK1 = buildACKChecksum(wrongACK, b"")

    
        err_val = (wrongACK, b"", chksumACK1)
        err_data = struct.Struct('I 8s 32s')
        err_packet = err_data.pack(*err_val)

        print("Sent Packet to Client: ", err_packet)
        sock.sendto(err_packet, addr)  