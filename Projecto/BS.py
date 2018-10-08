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
bufferSize  = 1024

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

		print(">> UDP server up and listening")

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(self):
		bytesAddressPair = self.UDPClientSocket.recvfrom(bufferSize)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Recieved: ", message)
		return (message.split(), addrstruct)
	
	def UDPSend(self, message, addrstruct):
		bytesToSend = str.encode(message)
		self.UDPClientSocket.sendto(bytesToSend, addrstruct)
		print(">> Sent: ", message)

	def UDPClose(self, socket):
		socket.close()
		print(">> UDP closed")
	
	def UDPSIGINT(self, _, __):
		self.UDPClose(self.UDPClientSocket)
		sys.exit()

	def UDPPseudoReceive(self):
		while not os.path.exists(TMP_UDP_FILE):
			time.sleep(0.1)
			
		msg = getDataFromFile(TMP_UDP_FILE)
		os.remove(TMP_UDP_FILE)
		return msg
		
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


# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:
	
	def startServer(self):

		self.TCPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)

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
	def TCPWrite(self, message): #PUT \n in the end pls
		bytesToSend = str.encode(message)
		nleft = len(bytesToSend)
		while (nleft):
			nleft -= self.connection.send(bytesToSend)
		print(">> Sent: ", message)

	def TCPRead(self):
		message = ""
		while (not len(message) or (len(message) and message[-1] != '\n')):
			message += bytes.decode(self.connection.recv(bufferSize))
		print(">> Received: ", message)
		return message[:-1].split() #erase \n from string

	def TCPClose(self):
		self.connection.close()
		self.TCPServerSocket.close()
		print(">> TCP closed")

	def TCPSIGINT(self, _, __):
		self.TCPClose()
		sys.exit()

	signal.signal(signal.SIGINT, TCPSIGINT)

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def authenticateUser(msgFromClient, TCPConnection):

	msgUser = msgFromClient[1]
	msgPw = msgFromClient[2]

	global currentUser
	path = USERPASS_FILE(msgUser)

	if checkFileExists(path):
		if getDataFromFile(path) == msgPw:
			TCPConnection.TCPWrite("AUR OK\n")
			currentUser = msgUser
		else:
			TCPConnection.TCPWrite("AUR NOK\n")
	
def writeBS(msgFromClient, TCPConnection):
	folder = msgFromClient[1]
	dir = USERFOLDER_PATH(currentUser, folder)
	numberOfFiles = int(msgFromClient[2])
	
	for i in range(numberOfFiles):
		j = 3 + 4 * i

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

	connection = TCPConnect().startServer()

	# READ MESSAGES
	while 1:
		msgFromClient = connection.TCPRead()

		command = msgFromClient[0]

		if command == "AUT":
			dictTCPFunctions["authenticateUser"](msgFromClient, connection)
		elif command == "UPL":
			dictTCPFunctions["writeBS"](msgFromClient, connection)
	sys.exit()

else:
	UDPConnect().run()
	sys.exit()