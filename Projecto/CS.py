import socket
import sys
import os


localIP     = socket.gethostbyname(socket.gethostname())

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

def UDPConnect():

	UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip

	UDPServerSocket.bind((localIP, localPort))

	print("UDP server up and listening")

	while 1:

		bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
		message = bytes.decode(bytesAddressPair[0]).split(" ") #string received
		bsAddr = bytesAddressPair[1]
		print(message)
		#address = bytesAddressPair[1]
		command = message[0]
		if command == 'REG':
			bsaddr = message[1]
			BSport = message[2]
			backupServers.append((bsaddr,BSport))
			bytesToSend = str.encode("RGR OK")
			UDPServerSocket.sendto(bytesToSend, bsAddr)
			print("+BS " + bsaddr + " " + BSport)

	UDPServerSocket.close()
   #clientMsg = "Message from Client:{}".format(message)
    	#lientIP  = "Client IP Address:{}".format(address)

    	#print(clientMsg)
    	#print(clientIP)



   		# Sending a reply to client




def TCPConnect():

	TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

	TCPServerSocket.bind((localIP, localPort))

	TCPServerSocket.listen(21)

	connection , addr = TCPServerSocket.accept()

	print("Client: ", addr)




pid = os.fork()
if pid == -1:
	print("erro no fork")
elif not pid:
	TCPConnect()
else:
	UDPConnect()



