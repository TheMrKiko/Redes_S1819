import socket
import sys

bsPort = sys.argv[2]
centralServer = sys.argv[4]

csPort   = sys.argv[6]
if csPort is None:
	csPort = 58013
else:
	csPort = int(csPort)


CSaddrPort   = (socket.gethostbyname(centralServer), csPort)
bufferSize  = 1024


registerMessage = "REG " + socket.gethostbyname(socket.gethostname()) + " " + str(bsPort)
bytesToSend = str.encode(registerMessage)
#msgFromServer       = "Hello UDP Client"

#bytesToSend         = str.encode(msgFromServer)

# Create a datagram socket

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Listen for incoming datagrams
#print("pila")
UDPClientSocket.sendto(bytesToSend ,CSaddrPort)
#print("pilaa")

msgFromServer = UDPClientSocket.recvfrom(bufferSize)
#print("pilaaa")
#if bytes.decode(msgFromServer[0]).split(" ")[1] == "NOK":
#	print("RGR ERR")

msg = "Message from Server {}".format(msgFromServer[0])


UDPClientSocket.close()
print(msg)
#clientMsg = "Message from Client:{}".format(message)
#lientIP  = "Client IP Address:{}".format(address)

#print(clientMsg)
#print(clientIP)



# Sending a reply to client
