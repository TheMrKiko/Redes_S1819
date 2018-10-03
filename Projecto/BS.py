import socket
import sys
import os

bsPort = sys.argv[2]
centralServer = sys.argv[4]

if len(sys.argv) < 7:
	csPort = 58013
else:
	csPort = int(sys.argv[6])

CSaddrPort   = (socket.gethostbyname(centralServer), csPort)
bufferSize  = 1024

registerMessage = "REG " + socket.gethostbyname(socket.gethostname()) + " " + str(bsPort)
bytesToSend = str.encode(registerMessage)

def UDPConnect():
	
	#msgFromServer       = "Hello UDP Client"

	#bytesToSend         = str.encode(msgFromServer)

	# Create a datagram socket

	UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

	# Listen for incoming datagrams

	UDPClientSocket.sendto(bytesToSend ,CSaddrPort)

	msgFromServer = UDPClientSocket.recvfrom(bufferSize)

	#if bytes.decode(msgFromServer[0]).split(" ")[1] == "NOK":
	#	print("RGR ERR")

	msg = "Message from Server {}".format(msgFromServer[0])

	UDPClientSocket.close()
	print(msg)



def TCPConnect():

	print("oi")
# Sending a reply to client

pid = os.fork()
if pid == -1:
	print("erro no fork")
elif not pid:
	TCPConnect()
	sys.exit()
else:
	UDPConnect()
	sys.exit()