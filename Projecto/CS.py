import socket
import sys


localIP     = "127.0.0.1"

localPort   = sys.argv[2] #command line port
print(localPort)
if localPort is None:
	localPort = 58013
else:
	localPort = int(localPort)

bufferSize  = 1024

backupServers = [] #store BS (ip, port)

#msgFromServer       = "Hello UDP Client"

#bytesToSend         = str.encode(msgFromServer)

# Create a datagram socket

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)



# Bind to address and ip

UDPServerSocket.bind((localIP, localPort))



print("UDP server up and listening")



# Listen for incoming datagrams


bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
message = bytes.decode(bytesAddressPair[0]).split(" ") #string received
print(message)
#address = bytesAddressPair[1]
command = message[0]
if command == 'REG':
	bsaddr = message[1]
	BSport = message[2]
	backupServers.append((bsaddr,BSport))
	bytesToSend = str.encode("RGR OK")
	UDPServerSocket.sendto(bytesToSend, (localIP, localPort))
	UDPServerSocket.close()
	print("+BS " + bsaddr + " " + BSport)
    #clientMsg = "Message from Client:{}".format(message)
    #lientIP  = "Client IP Address:{}".format(address)

    #print(clientMsg)
    #print(clientIP)



    # Sending a reply to client
