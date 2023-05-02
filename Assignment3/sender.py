import binascii
import socket
import struct
import sys
import hashlib


def buildACKChecksum(valueOfSeq, data):
    values = (valueOfSeq, data)
    packer = struct.Struct('I {}s'.format(len(data)))
    packed_data = packer.pack(*values)
    return bytes(hashlib.md5(packed_data).hexdigest(), encoding="UTF-8")




print('-------------------------------------------------------')

print('Enter Packet Size')
x = int(input())
print('Enter Number of Packets')
y = int(input())


ip = "127.0.0.1"
port = 5005
unpacker = struct.Struct('I 8s 32s')


input = "Hello this is a test string"
input = input.encode("utf-8") 
  
seqNo = 0  
packet_size = x
num_packets = y
data = []

for i in range(num_packets):
    chunk = input[i * packet_size : (i+1) * packet_size]
    if len(chunk) < packet_size:
       
        chunk += b'\x00' * (packet_size - len(chunk))
    data.append(chunk)



for chunk in data:



    chksum = buildACKChecksum(seqNo,chunk)

  
    Nvalues = (seqNo,chunk, chksum)
    packet = struct.Struct('I {}s 32s'.format(len(chunk)))
    packet = packet.pack(*Nvalues)


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  

    print("Sent Packet to Server: ", packet)
    sock.settimeout(0.009)  
    sock.sendto(packet, (ip, port))  

    while True:  

        try:

            data, address = sock.recvfrom(4096) 
            rpacket = unpacker.unpack(data)
            print("Received Message from Server: ({}, {}, {})".format(rpacket[0], rpacket[1].decode(), rpacket[2]))

            
            chksumR = buildACKChecksum(rpacket[0], rpacket[1])

            if rpacket[2] == chksumR and rpacket[0] == seqNo:  

                print("Checksums Match, Packet OK")

                sock.settimeout(None)  
                break  

            else:

                print("Packet is corrupted")

        except socket.timeout: 

            print("Packet Timer Expired")
            print("Sent Packet to Server: ", packet)

            sock.settimeout(0.009) 
            sock.sendto(packet, (ip, port))  

    

    if seqNo == 0: 

        seqNo = seqNo + 1

    elif seqNo == 1:

        seqNo = seqNo - 1


print("Sent {} packets of size {}".format(num_packets,packet_size))