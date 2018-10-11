import socket
import sys
import os
import signal
import json
import random
import time
from datetime import datetime

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
localIP = 'localhost'#socket.gethostbyname(socket.gethostname())
BUFFERSIZE = 1024

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
TCPOpens = []
UDPOpens = []

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
		try:
			self.UDPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)
		except:
			print("erro no socket")
		UDPOpens.append(self)

	def startServer(self):

		self.UDPServerSocket.bind((localIP, localPort))

		print(">> UDP server up and listening at ", (localIP, localPort))

		return self

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(self):
		bytesAddressPair = self.UDPServerSocket.recvfrom(BUFFERSIZE)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Received: ", message)
		return (message.split(), addrstruct)
	
	def UDPSend(self, message, addrstruct):
		bytesToSend = str.encode(message)
		self.UDPServerSocket.sendto(bytesToSend, addrstruct)
		print(">> Sent: ", message)

	def UDPClose(self):
		self.UDPServerSocket.close()
		print(">> UDP closed")

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

	def unregisterBS(self, ipBS,portBS,addrstruct):
		data = getDataFromFile(BACKUPLIST_FILE)
		print(portBS)
		for BS in data:
			print(BS)
			if BS[0] == ipBS and BS[1] == portBS:
					data.remove(BS)
					break
		self.UDPSend("UAR OK",addrstruct)
		
	# --------------------------- MAIN ---------------------------

	def runServer(self):
		dictUDPFunctions = {
			"registerBS": self.registerBS,
			"unregisterBS": self.unregisterBS
		}


		# READ MESSAGES
		while 1:
			message, addrstruct = self.UDPReceive()

			command = message[0]
			if command == 'REG':
				dictUDPFunctions["registerBS"](message, addrstruct)
			elif command =="UNR":
				dictUDPFunctions["unregisterBS"](message[1],message[2],addrstruct)
		# CLOSE CONNECTIONS
		self.UDPServerSocket.close()

def UDPSIGINT(_, __):
	for udp in UDPOpens:
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
	else:
		TCPConnection.TCPWriteMessage("AUR NEW\n")
		saveDataInFile(msgPw, path)
def deluser(socket):
	print("deluser")

def deleteDir(folder,socket):
	dir = USERFOLDER_PATH(currentUser, folder)
	dataBS = getDataFromFile(dir)
	os.remove(dir)
	msgDLB = "DLB " + currentUser + " " + folder
	UDPConnection = UDPConnect()
	UDPConnection.UDPSend(msgDLB, (dataBS[0], int(dataBS[2])))

def dirlist(socket):
	dir = USERFOLDERS_PATH(currentUser)
	if checkDirExists(dir):
		files = [name for name in os.listdir(dir)]
		numberOfFiles = len(files)
		msgLDR = "LDR " + str(numberOfFiles)
		for file in files:
			msgLDR += " " + file
		socket.TCPWriteMessage(msgLDR + "\n")
	else:
		socket.TCPWriteMessage("no dirs saved" + "\n")
def restore(folder, socket):
	dir = USERFOLDER_PATH(currentUser, folder)
	BS = getDataFromFile(dir) 
	msgRSR ="RSR " + BS[0] + " " + str(BS[2])
	socket.TCPWriteMessage(msgRSR + "\n")

def backupDir(msgFromClient, TCPConnection):
	numberOfFiles = int(msgFromClient[2])
	dir = USERFOLDER_PATH(currentUser, msgFromClient[1])
	infoFiles = []
	UDPConnection = UDPConnect()
	print("dir ", dir)
	if checkFileExists(dir):
		print("LSF")
		print(USERFOLDER_PATH(currentUser, msgFromClient[1]))
		BS = getDataFromFile(USERFOLDER_PATH(currentUser, msgFromClient[1]))
		print(BS)
		UDPConnection.UDPSend("LSF " + currentUser + " " + msgFromClient[1] , (BS[0], int(BS[2])))

		
		msgLFD = UDPConnection.UDPReceive()[0]
		dictFilesSaved = {} 
		print("msgLFD[1])", msgLFD[1])
		for i in range(int(msgLFD[1])):
			j = 2 + i * 4
			dictFilesSaved[msgLFD[j]] = [time.strptime(msgLFD[j+1] + " " + msgLFD[j+2], "%d.%m.%Y %H:%M:%S"), msgLFD[j+3]]

		dictFilesOfUser = {} 
		for i in range(numberOfFiles):
			j = 3 + i * 4
			dictFilesOfUser[msgFromClient[j]] = [time.strptime(msgFromClient[j+1] + " " + msgFromClient[j+2], "%d.%m.%Y %H:%M:%S"), msgFromClient[j+3]]
		msgBKR = ""
		numberOffilesToSend = 0
		
		print(dictFilesOfUser)
		print(dictFilesSaved)
		#datetime_object = time.strptime(msgFromClient[j+1] + " " + msgFromClient[j+2], "%d.%m.%Y %H:%M:%S")
		#print(datetime_object)
		
		for filesOfUser in dictFilesOfUser:
			for filesSaved in dictFilesSaved:
				if filesOfUser not in dictFilesSaved or filesOfUser == filesSaved and dictFilesSaved[filesOfUser] > dictFilesOfUser[filesSaved]:
					print("sending ", filesOfUser)
					msgBKR += " " + filesOfUser + " " + time.strftime("%d.%m.%Y %H:%M:%S", dictFilesOfUser[filesOfUser][0]) + " " + dictFilesOfUser[filesOfUser][1]
					numberOffilesToSend += 1
				else:
					print("not sending ", filesOfUser)

		"""for (filesOfUser, modDateUser) , (filesSaved, modDateSaved) in zip(dictFilesOfUser.items(), dictFilesSaved.items()):
			if filesOfUser not in dictFilesSaved or filesOfUser == filesSaved and modDateUser > modDateSaved:
				print("sending ", filesOfUser)
				msgBKR += " " + filesOfUser + " " + time.strftime("%d.%m.%Y %H:%M:%S", dictFilesOfUser[filesOfUser][0]) + " " + dictFilesOfUser[filesOfUser][1]
				numberOffilesToSend += 1
			else:
				print("not sending ", filesOfUser)"""
		#saber qual e o BS
		#saber quais os ficheiros a dar upda
		msgBKRfinal = "BKR " + BS[0] + " " + str(BS[1]) + " " + str(numberOffilesToSend) + msgBKR

		TCPConnection.TCPWriteMessage(msgBKRfinal+"\n")
	else:
		bsServers = getDataFromFile(BACKUPLIST_FILE)
		if len(bsServers):  #if exists BS servers
			chosen = random.choice(bsServers)
			pw = getDataFromFile(USERPASS_FILE(currentUser))
			msg = "LSU " + currentUser + " " + pw
		
			UDPConnection.UDPSend(msg, (chosen[0], int(chosen[2])))

			msgFromBs, addrstruct = UDPConnection.UDPReceive()

			if msgFromBs[1] == "OK":
				msgUser = "BKR " + chosen[0] + " " + chosen[1]
				for i in range(2, len(msgFromClient)):
					msgUser += " " +  msgFromClient[i]
				TCPConnection.TCPWriteMessage(msgUser + "\n")

				saveDataInFile([chosen[0], int(chosen[1]), int(chosen[2])], USERFOLDER_PATH(currentUser, msgFromClient[1]))
		else:
			print("Arranja BS")
			return
	
	UDPConnection.UDPClose()

	#MANDA CREDENTIALS DO USER E VERIFICA QUE FILES TÊM DE SER UPDATED 
	#VÊ EM Q BS O USER TEM DE MANDAR OS FICHEIROS E MANDA O ENDEREÇO DO BS AO USER
	#USER FECHA TCP COM CS E ABRE NOVA TCP COM BS
	#USER AUTENTICA NO BS



# --------------------------- MAIN ---------------------------
dictTCPFunctions = {
	"authenticateUser": authenticateUser,
	"backupDir": backupDir,
	"dirlist": dirlist,
	"restore": restore,
	"deluser": deluser,
	"deleteDir": deleteDir


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
		msgFromClient = connection.TCPReadMessage()

		command = msgFromClient[0]

		if command == "AUT":
			dictTCPFunctions["authenticateUser"](msgFromClient, connection)	
		elif command == "BCK":
			dictTCPFunctions["backupDir"](msgFromClient, connection)
		elif command == "LSD":
			dictTCPFunctions["dirlist"](connection)
		elif command == "RST":
			dictTCPFunctions["restore"](msgFromClient[1], connection)
		elif command == "DLU":
			dictTCPFunctions["deluser"](connection)
		elif command == "DEL":
			dictTCPFunctions["deleteDir"](msgFromClient[1],connection)

	sys.exit()
else:
	signal.signal(signal.SIGINT, UDPSIGINT)
	UDPConnection = UDPConnect().startServer()
	UDPConnection.runServer()
	sys.exit()