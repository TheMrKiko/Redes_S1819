import socket
import sys
import os
import signal
import json
import time

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
BSPort = int(sys.argv[2])
CSName = sys.argv[4]

if len(sys.argv) < 7:
	CSPort = 58013
else:
	CSPort = int(sys.argv[6])

CSAddrStruct = (socket.gethostbyname(CSName), CSPort)
localIP = socket.gethostbyname(socket.gethostname())
BUFFERSIZE  = 1024
TCPOpens = []
UDPPOpens = []

BSDATA_PATH = './bsdata_' + str(BSPort)
BACKUPLIST_FILE = BSDATA_PATH + '/backup.txt'
TMP_UDP_FILE = BSDATA_PATH + '/UDPtempmessage.txt'
USERPASS_FILE = lambda user : BSDATA_PATH + '/users/user_'+ user + '.txt'
USERFOLDERS_PATH = lambda user : BSDATA_PATH + '/user_' + user
USERFOLDER_PATH = lambda user, folder : USERFOLDERS_PATH(user) + '/' + folder

def checkFileExists(filename):
	return os.path.isfile(filename)

def checkDirExists(path):
	return os.path.isdir(path)
	
def getDataFromFile(filename):
	if checkFileExists(filename):
		fp = open(filename, 'r')
		ds = json.load(fp)
		fp.close()
		print(">> Loaded: ", ds)
		return ds

def saveDataInFile(data, filename):
	os.makedirs(os.path.dirname(filename), exist_ok = True)
	fp = open(filename, 'w')
	json.dump(data, fp)
	fp.close()
	print(">> Saved: ", data)

# -------------------------------- PROCESS FOR UDP --------------------------------
class UDPConnect:

	def __init__(self):
		self.UDPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)

		UDPPOpens.append(self)

		print(">> UDP server up and listening")

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(self):
		bytesAddressPair = self.UDPClientSocket.recvfrom(BUFFERSIZE)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Recieved: ", message)
		return (message.split(), addrstruct)
	
	def UDPSend(self, message, addrstruct):
		bytesToSend = str.encode(message)
		self.UDPClientSocket.sendto(bytesToSend, addrstruct)
		print(">> Sent: ", message)

	def UDPClose(self):
		self.UDPClientSocket.close()
		print(">> UDP closed")
		
	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def init(self):
		message = "REG " + socket.gethostbyname(socket.gethostname()) + " " + str(BSPort)
		self.UDPSend(message, CSAddrStruct)
		msg, addrstruct = self.UDPReceive()
        
	def registerNewUser(self,user,pw,addrstruct):
		saveDataInFile(pw,USERPASS_FILE(user))
		self.UDPSend("LUR OK", addrstruct)

	def run(self):

		dictUDPFunctions = {
			"registerNewUser": self.registerNewUser
		}

		# --------------------------- MAIN ---------------------------
		self.init()

		# READ MESSAGES
		while 1:
			message, addrstruct = self.UDPReceive()

			command = message[0]
			if command == 'LSU':
				dictUDPFunctions["registerNewUser"](message[1], message[2], addrstruct)
			
		# CLOSE CONNECTIONS
		self.UDPClientSocket.close()

def UDPSIGINT(_, __):
	for udp in UDPPOpens:
		udp.UDPClose()
	sys.exit()

# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:
	
	def __init__(self):
		self.TCPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
		self.connection = self.TCPServerSocket
		TCPOpens.append(self)

	
	def startServer(self):
		self.TCPServerSocket.bind((localIP, BSPort))

		self.TCPServerSocket.listen(21)

		while 1:
			self.connection, self.addr = self.TCPServerSocket.accept()

			pid = os.fork()
			if pid == -1:
				print("erro no fork")
			elif pid:
					continue

			print(">> Client: ", self.addr)

			return self
	
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPWrite(self, tosend):
		nleft = len(tosend)
		while (nleft):
			nleft -= self.connection.send(tosend)

	def TCPWriteMessage(self, message): #PUT \n in the end pls
		bytesToSend = str.encode(message)
		self.TCPWrite(bytesToSend)
		print(">> Sent: ", message)

	def TCPRead(self, bufferSize):
		return self.connection.recv(bufferSize)

	def TCPReadMessage(self):
		message = self.TCPReadStepByStep(BUFFERSIZE, '\n')
		print(">> Received: ", message)
		return message.split()

	def TCPReadWord(self):
		return self.TCPReadStepByStep(1, ' ')

	def TCPReadStepByStep(self, bufferSize, end):
		message = ""
		while (not len(message) or (len(message) and message[-1] != end)):
			message += bytes.decode(self.TCPRead(bufferSize))
		return message[:-1] #erase end from string

	def TCPReadFile(self, filename, filesize):
		with open(filename, "wb+") as fp:
			while(filesize):
				bytes = self.TCPRead()
				filesize -= len(bytes)
				fp.write(bytes)

	def TCPClose(self):
		self.connection.close()
		self.TCPServerSocket.close()
		print(">> TCP closed")

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def TCPSIGINT(_, __):
	for tcp in TCPOpens:
		tcp.TCPClose()
	sys.exit()

def authenticateUser(msgFromClient, TCPConnection):

	msgUser = msgFromClient[1]
	msgPw = msgFromClient[2]

	global currentUser
	path = USERPASS_FILE(msgUser)

	if checkFileExists(path):
		if getDataFromFile(path) == msgPw:
			TCPConnection.TCPWriteMessage("AUR OK\n")
			currentUser = msgUser
		else:
			TCPConnection.TCPWriteMessage("AUR NOK\n")
	
def writeBS(msgFromClient, TCPConnection):
	folder = msgFromClient[1]
	dir = USERFOLDER_PATH(currentUser, folder)
	numberOfFiles = int(msgFromClient[2])

	for i in range(numberOfFiles):
		name =  3 + i * 4
		#TCPConnection.TCPReadFile(dir+"/"+msgFromClient[], msgFromClient[])

# --------------------------- MAIN ---------------------------

dictTCPFunctions = {
	"authenticateUser": authenticateUser,
	"writeBS": writeBS
}


# ------------------------ SEPERATION OF PROCESSES ------------------------
pid = os.fork()
if pid == -1:
	print("erro no fork")
elif not pid:

	signal.signal(signal.SIGINT, TCPSIGINT)
	connection = TCPConnect().startServer()

	# READ MESSAGES
	while 1:
		msgFromClient = connection.TCPReadWord()

		command = msgFromClient

		if command == "AUT":
			msg = list(msgFromClient).append(connection.TCPReadMessage())
			print("oi ", msg)
			dictTCPFunctions["authenticateUser"](msg, connection)
		elif command == "UPL":
			dictTCPFunctions["writeBS"](msgFromClient, connection)
	sys.exit()

else:
	signal.signal(signal.SIGINT, UDPSIGINT)
	UDPConnect().run()
	sys.exit()