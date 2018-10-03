import socket
import sys
import os
import signal

# ------------------------ VARS AND CONSTANTS ------------------------
localIP = "localhost"#socket.gethostbyname(socket.gethostname())
bufferSize  = 1024
backupServers = [] #store BS (ip, port)

#store user (nick, pw)
users = [] #case with no users
#users = [("123", "xxx") , ("234", "abc")] #wrong login
#users = [("123" , "abc")] #right login

# ------------------------ ARGS READING ------------------------
if len(sys.argv) < 3:
	localPort = 58013
else:
	localPort = int(sys.argv[2]) #command line port

print(localPort)

# -------------------------------- PROCESS FOR UDP --------------------------------
def UDPConnect():

	UDPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)

	# Bind to address and ip
	UDPServerSocket.bind((localIP, localPort))

	print("UDP server up and listening")

	# FUNTIONS TO COMMUNICATE
	def UDPReceive(socket):
		bytesAddressPair = socket.recvfrom(bufferSize)
		message = bytes.decode(bytesAddressPair[0]).split() #string received
		addr = bytesAddressPair[1]
		return (message, addr)
	
	def UDPSend(message, socket, address):
		bytesToSend = str.encode(message)
		UDPServerSocket.sendto(bytesToSend, address)

	def UDPClose(socket):
		socket.close()
		print("tupd closed")
	
	def UDPSIGINT(_, __):
		UDPClose(UDPServerSocket)
		sys.exit()

	signal.signal(signal.SIGINT, UDPSIGINT)


	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def registerBS(message, address):
		BSaddr = message[1]
		BSport = message[2]
		backupServers.append((BSaddr, BSport))
		UDPSend("RGR OK", UDPServerSocket, address)
		print("+BS " + BSaddr + " " + BSport)

	# --------------------------- MAIN ---------------------------
	dictUDPFunctions = {
		"registerBS": registerBS
	}

	# READ MESSAGES
	while 1:
		message, address = UDPReceive(UDPServerSocket)
		print(message)

		command = message[0]
		if command == 'REG':
			dictUDPFunctions["registerBS"](message, address)

	# CLOSE CONNECTIONS
	UDPServerSocket.close()
	#clientMsg = "Message from Client:{}".format(message)
    #lientIP  = "Client IP Address:{}".format(address)

    #print(clientMsg)
    #print(clientIP)

# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

# -------------------------------- PROCESS FOR TCP --------------------------------
def TCPConnect():

	TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

	TCPServerSocket.bind((localIP, localPort))

	TCPServerSocket.listen(21)
    
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPSend(message, connection):
		bytesToSend = str.encode(message)
		nleft = len(bytesToSend)
		while (nleft):
			nleft -= connection.send(bytesToSend)

	def TCPRead(connection):
		msgFromClient = ""
		while (not len(msgFromClient) or (len(msgFromClient) and msgFromClient[-1] != '\n')):
			msgFromClient += bytes.decode(connection.recv(bufferSize))
		print("recebi" + msgFromClient)
		return msgFromClient[:-1] #erase \n from string

	def TCPClose(server, clients):
		clients.close()
		server.close()
		print("tcp closed")
	
	def TCPSIGINT(_, __):
		TCPClose(TCPServerSocket, connection)
		sys.exit()

	signal.signal(signal.SIGINT, TCPSIGINT)

	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def authenticateUser(msgFromClient):
		#print("entrei")
		msgUser = msgFromClient[1]
		msgPw = msgFromClient[2]
		if (msgUser, msgPw) in users: #successful login
			#print("valido")
			TCPSend("AUR OK\n", connection)
		else:
			found = False
			for i in range(len(users)): #checks if pw is ok
				if msgUser == users[i][0] and msgPw != users[i][1]:
					found = True
					TCPSend("AUR NOK\n", connection)
			if not found: #new user
				TCPSend("AUR NEW\n", connection)
	
	# --------------------------- MAIN ---------------------------
	dictTCPFunctions = {
		"authenticateUser": authenticateUser
		}

	connection, addr = TCPServerSocket.accept()

	print("Client: ", addr)

	# READ MESSAGES

	while 1:
		msgFromClient = TCPRead(connection).split()

		command = msgFromClient[0]

		#print(command)
		if command == "AUT":
			dictTCPFunctions["authenticateUser"](msgFromClient)
	
	# CLOSE CONNECTIONS
	TCPClose(TCPServerSocket, connection)


# ------------------------ SEPERATION OF PROCESSES ------------------------
pid = os.fork()
if pid == -1:
	print("erro no fork")
elif not pid:
	TCPConnect()
	sys.exit()
else:
	UDPConnect()
	sys.exit()
