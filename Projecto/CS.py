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

#dirs to store info for users and backups
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
TCPOpens = [] #array of tcp connections
UDPOpens = [] #array of udp connections


#creating file to store BS information using json library: backupServers
os.makedirs(os.path.dirname(BACKUPLIST_FILE), exist_ok = True)
fp = open(BACKUPLIST_FILE, 'w')
json.dump(backupServers, fp)
fp.close()

#default port
if len(sys.argv) < 3:
	localPort = 58013
else:
	localPort = int(sys.argv[2])

#verification if a file exists
def checkFileExists(filename):
	try:
		return os.path.isfile(filename)
	except:
		print("File not found")

#verification if a dir exists
def checkDirExists(path):
	try:
		return os.path.isdir(path)
	except:
		print("Directory not found")
	
#opens a file and receives the data structure saved using json library
def getDataFromFile(filename):
	if checkFileExists(filename):
		fp = open(filename, 'r')
		ds = json.load(fp)
		fp.close()
		print(">> Loaded: ", ds)
		return ds

#writes a data structure in a file using json library
def saveDataInFile(data, filename):
	try:
		os.makedirs(os.path.dirname(filename), exist_ok = True)
		fp = open(filename, 'w')
		json.dump(data, fp)
		fp.close()
		print(">> Saved: ", data)
	except:
		print("Error saving data in file")

# -------------------------------- PROCESS FOR UDP --------------------------------
class UDPConnect:

	def __init__(self):
		try:
			self.UDPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)
			UDPOpens.append(self)
		except:
			print("erro no socket")

	def startServer(self):
		try:
			self.UDPServerSocket.bind((localIP, localPort))

			print(">> UDP server up and listening at ", (localIP, localPort))

			return self
		except:
			print("error starting UDP server")

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(self):
		try:
			bytesAddressPair = self.UDPServerSocket.recvfrom(BUFFERSIZE)
			message = bytes.decode(bytesAddressPair[0])
			addrstruct = bytesAddressPair[1]
			print(">> Received: ", message)
			return (message.split(), addrstruct)
		except:
			print("error receiving UDP")
	
	def UDPSend(self, message, addrstruct):
		try:
			bytesToSend = str.encode(message)
			self.UDPServerSocket.sendto(bytesToSend, addrstruct)
			print(">> Sent: ", message)
		except:
			print("error sending UDP")

	def UDPClose(self):
		try:
			self.UDPServerSocket.close()
			print(">> UDP closed")
		except:
			print("error closing UDP")

	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def registerBS(self, message, addressstruct):
		BSaddr = message[1]
		BSport = message[2]
		flag = 0
		data = getDataFromFile(BACKUPLIST_FILE)
		for bs in data: #checking if BS was already stored
			if bs[0] == BSaddr and bs[1] ==BSport:
				print("BS already registered")
				flag = 1
		if len(message) != 3: #syntax checking
			print("RGR ERR")
		elif flag != 1:#if new BS
			data.append([BSaddr, BSport,addressstruct[1]])
			saveDataInFile(data, BACKUPLIST_FILE)
			self.UDPSend("RGR OK", addressstruct)
			print("+BS " + BSaddr + " " + BSport)
		else: #BS already registered
			print("RGR NOK")

	def unregisterBS(self, message,addrstruct):
		data = getDataFromFile(BACKUPLIST_FILE)
		print("data", data)
		print("msg", message)
		if len(message)!=3: #syntax checking
			msgERR = "UAR ERR" 
			self.UDPSend("UAR ERR",addrstruct)
			return
		for BS in data:
			print(BS)
			if BS[0] == message[1] and BS[1] == message[2]: #if BS in saved BS's
				data.remove(BS)
				self.UDPSend("UAR OK",addrstruct)
				return
		self.UDPSend("UAR NOK",addrstruct) #BS not known to CS
		
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
				dictUDPFunctions["unregisterBS"](message,addrstruct)
		# CLOSE CONNECTIONS
		self.UDPServerSocket.close()

def UDPSIGINT(_, __): #signal ^C handler
	for udp in UDPOpens:
		udp.UDPClose()
	sys.exit()

# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:

	def __init__(self):
		try:
			self.TCPServerSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
			self.connection = self.TCPServerSocket
			TCPOpens.append(self)
		except:
			print("error starting TCP")

	
	def startServer(self):
		try:
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
		except:
			print("error starting TCP server")
	
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPWrite(self, tosend):
		try:
			nleft = len(tosend)
			while (nleft):
				nleft -= self.connection.send(tosend)
		except:
			print("error writing tcp")

	def TCPWriteMessage(self, message): #PUT \n in the end pls
		try:
			bytesToSend = str.encode(message)
			self.TCPWrite(bytesToSend)
			print(">> Sent: ", message)
		except:
			print("error writing message")

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
		try:
			self.connection.close()
			self.TCPServerSocket.close()
			print(">> TCP closed")
		except:
			print("error closing TCP")


# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def TCPSIGINT(_, __): #^C handler
	for tcp in TCPOpens:
		tcp.TCPClose()
	sys.exit()

def authenticateUser(msgFromClient, TCPConnection):
	global currentUser
	print(currentUser)
	msgUser = msgFromClient[1]
	msgPw = msgFromClient[2]

	path = USERPASS_FILE(msgUser) #file with pw of user stored

	if checkFileExists(path): #if already registered user
		if getDataFromFile(path) == msgPw:
			TCPConnection.TCPWriteMessage("AUR OK\n")
			currentUser = msgUser
		else: #wrong pw
			TCPConnection.TCPWriteMessage("AUR NOK\n")
	else: #new user
		TCPConnection.TCPWriteMessage("AUR NEW\n")
		saveDataInFile(msgPw, path)
	print(currentUser)

def deluser(socket):
	dir = USERFOLDERS_PATH(currentUser) #dir with files named after dirs stored in BS
	print(dir)
	if checkDirExists(dir):
		dirs = [name for name in os.listdir(dir)]
		if len(dirs) > 0: #if dirs still in BS
			socket.TCPWriteMessage("DLR NOK\n")
		else:
			os.rmdir(dir) #remove user info stored in CS
			os.remove(USERPASS_FILE(currentUser))

			socket.TCPWriteMessage("DLR OK\n")
	
def deleteDir(folder,socket):
	dir = USERFOLDER_PATH(currentUser, folder)
	dataBS = getDataFromFile(dir) #check which BS the dir is stored
	os.remove(dir)
	msgDLB = "DLB " + currentUser + " " + folder
	UDPConnection = UDPConnect()
	UDPConnection.UDPSend(msgDLB, (dataBS[0], int(dataBS[2]))) #ask BS to delete
	msgDBR = UDPConnection.UDPReceive()[0]
	if msgDBR[1] == "OK":
		socket.TCPWriteMessage("DDR OK\n")
	else:
		socket.TCPWriteMessage("DDR NOK\n")
	UDPConnection.UDPClose()


def filelist(folder, socket):
	dir = USERFOLDER_PATH(currentUser, folder)
	dataBS = getDataFromFile(dir) #check which BS the dir is stored
	if checkFileExists(dir):
		UDPConnection = UDPConnect()
		UDPConnection.UDPSend("LSF " + currentUser + " " + folder , (dataBS[0], int(dataBS[2])))
		listLFD = UDPConnection.UDPReceive()[0]
		msgLFD = ""
		for data in listLFD:
			msgLFD += data + " "
			if data == "LFD":
				msgLFD += dataBS[0] + " " + str(dataBS[2]) + " "
		socket.TCPWriteMessage(msgLFD + "\n")
	else:
		socket.TCPWriteMessage("LFD NOK" + "\n")
	

def dirlist(socket):
	print(currentUser)
	dir = USERFOLDERS_PATH(currentUser)
	if checkDirExists(dir):
		files = [name for name in os.listdir(dir)]
		numberOfFiles = len(files)
		msgLDR = "LDR " + str(numberOfFiles)
		for file in files:
			msgLDR += " " + file
		socket.TCPWriteMessage(msgLDR + "\n")
	else:
		socket.TCPWriteMessage("LSD 0" + "\n")

def restore(folder, socket):
	dir = USERFOLDER_PATH(currentUser, folder)
	print(dir)
	print("dir ", checkDirExists(dir))
	if checkFileExists(dir):
		BS = getDataFromFile(dir) 
		msgRSR ="RSR " + BS[0] + " " + str(BS[1])
	else:
		msgRSR = "RSR EOF"
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
		
		for filesOfUser in dictFilesOfUser:
			for filesSaved in dictFilesSaved:
				if filesOfUser not in dictFilesSaved or filesOfUser == filesSaved and dictFilesSaved[filesOfUser] > dictFilesOfUser[filesSaved]:
					print("sending ", filesOfUser)
					msgBKR += " " + filesOfUser + " " + time.strftime("%d.%m.%Y %H:%M:%S", dictFilesOfUser[filesOfUser][0]) + " " + dictFilesOfUser[filesOfUser][1]
					numberOffilesToSend += 1
				else:
					print("not sending ", filesOfUser)

	
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

# --------------------------- MAIN ---------------------------
dictTCPFunctions = {
	"authenticateUser": authenticateUser,
	"backupDir": backupDir,
	"dirlist": dirlist,
	"restore": restore,
	"deluser": deluser,
	"deleteDir": deleteDir,
	"filelist": filelist


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
			print(connection)
			dictTCPFunctions["dirlist"](connection)
		elif command == "RST":
			dictTCPFunctions["restore"](msgFromClient[1], connection)
		elif command == "DLU":
			dictTCPFunctions["deluser"](connection)
		elif command == "DEL":
			dictTCPFunctions["deleteDir"](msgFromClient[1],connection)
		elif command == "LSF":
			dictTCPFunctions["filelist"](msgFromClient[1], connection)

	sys.exit()
else:
	signal.signal(signal.SIGINT, UDPSIGINT)
	UDPConnection = UDPConnect().startServer()
	UDPConnection.runServer()
	sys.exit()