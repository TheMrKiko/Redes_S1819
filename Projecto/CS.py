import socket
import sys
import os
import signal
import json
import random
import time

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
localIP = "localhost"#socket.gethostbyname(socket.gethostname())
bufferSize = 1024

CSDATA_PATH = './csdata'
BACKUPLIST_FILE = CSDATA_PATH + '/backup.txt'
TMP_UDP_FILE = CSDATA_PATH + '/UDPtempmessage.txt'
USERPASS_FILE = lambda user : CSDATA_PATH + '/users/user_'+ user + '.txt'
USERFOLDERS_PATH = lambda user : CSDATA_PATH + '/user_' + user
USERFOLDER_PATH = lambda user, folder : USERFOLDERS_PATH(user) + '/' + folder


#case with no users
#users = [["123", "xxx"] , ["234", "abc"]] #wrong login
#users = [["123" , "abc"]] #right login

backupServers = [] #store BS (ip, port) 
currentUser = None

os.makedirs(os.path.dirname(BACKUPLIST_FILE), exist_ok = True)
fp = open(BACKUPLIST_FILE, 'w')
json.dump(backupServers, fp)
fp.close()

if len(sys.argv) < 3:
	localPort = 58013
else:
	localPort = int(sys.argv[2])

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
		self.UDPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)

		self.UDPServerSocket.bind((localIP, localPort))

		print(">> UDP server up and listening")

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(self):
		bytesAddressPair = self.UDPServerSocket.recvfrom(bufferSize)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Recieved: ", message)
		return (message.split(), addrstruct)
	
	def UDPSend(self, message, addrstruct):
		bytesToSend = str.encode(message)
		self.UDPServerSocket.sendto(bytesToSend, addrstruct)
		print(">> Sent: ", message)

	def UDPClose(self, socket):
		socket.close()
		print(">> UDP closed")
	
	def UDPSIGINT(self, _, __):
		self.UDPClose(self.UDPServerSocket)
		sys.exit()

	def UDPPseudoReceive(self):
		while not os.path.exists(TMP_UDP_FILE):
			time.sleep(0.1)
		
		msg = getDataFromFile(TMP_UDP_FILE)
		os.remove(TMP_UDP_FILE)
		return msg


	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def registerBS(self, message, addressstruct):
		BSaddr = message[1]
		BSport = message[2]
		print(addressstruct)		
		data = getDataFromFile(BACKUPLIST_FILE)
		data.append([BSaddr, BSport,addressstruct[1]])
		saveDataInFile(data, BACKUPLIST_FILE)
		self.UDPSend("RGR OK", addressstruct)
		print("+BS " + BSaddr + " " + BSport)

	def saveToTmpFile(self,message):
		saveDataInFile(message,TMP_UDP_FILE)
	# --------------------------- MAIN ---------------------------
	def run(self):
		dictUDPFunctions = {
			"registerBS": self.registerBS,
			"saveToTMPFile": self.saveToTmpFile
		}

		signal.signal(signal.SIGINT, self.UDPSIGINT)

		# READ MESSAGES
		while 1:
			message, addrstruct = self.UDPReceive()

			command = message[0]
			if command == 'REG':
				dictUDPFunctions["registerBS"](message, addrstruct)
			if command == 'LUR':
				dictUDPFunctions["saveToTMPFile"](message)
		# CLOSE CONNECTIONS
		self.UDPServerSocket.close()

# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:
	
	def startServer(self):

		self.TCPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)

		self.TCPServerSocket.bind((localIP, localPort))

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
		print(">> Recieved: ", message)
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
	else:
		TCPConnection.TCPWrite("AUR NEW\n")
		saveDataInFile(msgPw, path)


def backupDir(msgFromClient, TCPConnection, UDPConnection):
	numberOfFiles = int(msgFromClient[2])
	dir = USERFOLDER_PATH(currentUser, msgFromClient[1])
	infoFiles = []

	if checkDirExists(dir):
		print(1)
		#saber qual e o BS
		#saber quais os ficheiros a dar upda
	else:
		bsServers = getDataFromFile(BACKUPLIST_FILE)
		if len(bsServers):  #if exists BS servers
			chosen = random.choice(bsServers)
			pw = getDataFromFile(USERPASS_FILE(currentUser))
			msg = "LSU " + currentUser + " " + pw
		
			UDPConnection.UDPSend(msg, (chosen[0],int(chosen[2])))
			msgFromBs = UDPConnection.UDPPseudoReceive()
			if msgFromBs[1] == "OK":
				msgUser = "BKR " + chosen[0] + " " + chosen[1]
				for i in range(2, len(msgFromClient)):
					msgUser += " " +  msgFromClient[i]
				#msgFromClient[2:]
				TCPConnection.TCPWrite(msgUser + "\n")
		else:
			print("Arranja BS para mandar esta merda")
			return

	for i in range(numberOfFiles):
		j = 3 + i*4
		infoFiles.append([msgFromClient[j], msgFromClient[j + 1], msgFromClient[j + 2], msgFromClient[j + 3]])
	#if (infoFiles)
	print(infoFiles)
	

	#MANDA CREDENTIALS DO USER E VERIFICA QUE FILES TÊM DE SER UPDATED 
	#VÊ EM Q BS O USER TEM DE MANDAR OS FICHEIROS E MANDA O ENDEREÇO DO BS AO USER
	#USER FECHA TCP COM CS E ABRE NOVA TCP COM BS
	#USER AUTENTICA NO BS


# --------------------------- MAIN ---------------------------
dictTCPFunctions = {
	"authenticateUser": authenticateUser,
	"backupDir": backupDir
	}


# ------------------------ SEPERATION OF PROCESSES ------------------------

UDPConnection = UDPConnect()

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
		
		elif command == "BCK":
			dictTCPFunctions["backupDir"](msgFromClient, connection, UDPConnection)

	sys.exit()
else:
	UDPConnection.run()
	sys.exit()