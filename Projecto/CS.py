import socket
import sys
import os


localIP     = "localhost"#socket.gethostbyname(socket.gethostname())

if len(sys.argv) < 3:
	localPort = 58013
else:
	localPort = int(sys.argv[2]) #command line port

print(localPort)
bufferSize  = 1024

backupServers = [] #store BS (ip, port)


#store user (nick, pw)

users = [] #case with no users
#users = [("123", "xxx") , ("234", "abc")] #wrong login
#users = [("123" , "abc")] #right login


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

	msgFromClient = " "
	while (msgFromClient[-1] != '\n'):
		msgFromClient += bytes.decode(connection.recv(bufferSize))
	msgFromClient = msgFromClient[1:-1] #erase space and \n from string
	#print("recebi" + msgFromClient)
	msgFromClient = msgFromClient.split(" ")
	command = msgFromClient[0]
	#print(command)
	if command == "AUT":
		#print("entrei")
		msgUser = msgFromClient[1]
		msgPw = msgFromClient[2]
		if (msgUser, msgPw) in users: #successful login
			#print("valido")
			bytesToSend = str.encode("AUR OK\n")
			nleft = len(bytesToSend)
			while (nleft):
				nleft -= connection.send(bytesToSend)
		else:
			found = False
			for i in range(len(users)): #checks if pw is ok
				if msgUser == users[i][0] and msgPw != users[i][1]:
					found = True
					bytesToSend = str.encode("AUR NOK\n")
					nleft = len(bytesToSend)
					while (nleft):
						nleft -= connection.send(bytesToSend)
			if not found: #new user
				bytesToSend = str.encode("AUR NEW\n")
				nleft = len(bytesToSend)
				while (nleft):
					nleft -= connection.send(bytesToSend)
	connection.close()
	TCPServerSocket.close()
	#print("tcp closed")

pid = os.fork()
if pid == -1:
	print("erro no fork")
elif not pid:
	TCPConnect()
	sys.exit()
else:
	UDPConnect()
	sys.exit()
