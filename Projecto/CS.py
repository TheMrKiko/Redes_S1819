import socket
import sys
import os
import signal

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
localIP = "localhost"#socket.gethostbyname(socket.gethostname())
bufferSize  = 1024
backupServers = [] #store BS (ip, port)
users = [] #store user (nick, pw)
#case with no users
#users = [("123", "xxx") , ("234", "abc")] #wrong login
#users = [("123" , "abc")] #right login

if len(sys.argv) < 3:
	localPort = 58013
else:
	localPort = int(sys.argv[2])

# -------------------------------- PROCESS FOR UDP --------------------------------
def UDPConnect():

	UDPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)

	UDPServerSocket.bind((localIP, localPort))

	print(">> UDP server up and listening")

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(socket):
		bytesAddressPair = socket.recvfrom(bufferSize)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Recieved: ", message)
		return (message.split(), addrstruct)
	
	def UDPSend(message, socket, addrstruct):
		bytesToSend = str.encode(message)
		socket.sendto(bytesToSend, addrstruct)
		print(">> Sent: ", message)

	def UDPClose(socket):
		socket.close()
		print(">> UDP closed")
	
	def UDPSIGINT(_, __):
		UDPClose(UDPServerSocket)
		sys.exit()

	signal.signal(signal.SIGINT, UDPSIGINT)

	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def registerBS(message, addressstruct):
		BSaddr = message[1]
		BSport = message[2]
		backupServers.append((BSaddr, BSport))
		UDPSend("RGR OK", UDPServerSocket, addressstruct)
		print("+BS " + BSaddr + " " + BSport)

	# --------------------------- MAIN ---------------------------
	dictUDPFunctions = {
		"registerBS": registerBS
	}

	# READ MESSAGES
	while 1:
		message, addrstruct = UDPReceive(UDPServerSocket)

		command = message[0]
		if command == 'REG':
			dictUDPFunctions["registerBS"](message, addrstruct)

	# CLOSE CONNECTIONS
	UDPServerSocket.close()

# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

# -------------------------------- PROCESS FOR TCP --------------------------------
def TCPConnect():

	TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

	TCPServerSocket.bind((localIP, localPort))

	TCPServerSocket.listen(21)

	connection, addr = TCPServerSocket.accept()

	print(">> Client: ", addr)
    
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPWrite(message, connection): #PUT \n in the end pls
		bytesToSend = str.encode(message)
		nleft = len(bytesToSend)
		while (nleft):
			nleft -= connection.send(bytesToSend)
		print(">> Sent: ", message)

	def TCPRead(connection):
		message = ""
		while (not len(message) or (len(message) and message[-1] != '\n')):
			message += bytes.decode(connection.recv(bufferSize))
		print(">> Recieved: ", message)
		return message[:-1].split() #erase \n from string

	def TCPClose(socket, clients):
		clients.close()
		socket.close()
		print(">> TCP closed")
	
	def TCPSIGINT(_, __):
		TCPClose(TCPServerSocket, connection)
		sys.exit()

	signal.signal(signal.SIGINT, TCPSIGINT)

	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def authenticateUser(msgFromClient):

		msgUser = msgFromClient[1]
		msgPw = msgFromClient[2]
		if (msgUser, msgPw) in users: #successful login
			TCPWrite("AUR OK\n", connection)
		else:
			found = False
			for i in range(len(users)): #checks if pw is ok
				if msgUser == users[i][0] and msgPw != users[i][1]:
					found = True
					TCPWrite("AUR NOK\n", connection)
			if not found: #new user
				TCPWrite("AUR NEW\n", connection)
	
	# --------------------------- MAIN ---------------------------
	dictTCPFunctions = {
		"authenticateUser": authenticateUser
		}

	# READ MESSAGES
	while 1:
		msgFromClient = TCPRead(connection)

		command = msgFromClient[0]

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
