import socket
import sys
import os
import signal
import json
import time
import shutil

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
	try:
		return os.path.isfile(filename)
	except:
		print("file not found")

def checkDirExists(path):
	try:
		return os.path.isdir(path)
	except:
		print("directoy not found")
	
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

def receiveFileAndWrite(dir, numberOfFiles, TCPConnection):

	data = {}

	for i in range(numberOfFiles):
		name = TCPConnection.TCPReadWord()
		date = TCPConnection.TCPReadWord()
		hour = TCPConnection.TCPReadWord()
		size = int(TCPConnection.TCPReadWord())
		print("ola crl", name, date, hour, size)

		TCPConnection.TCPReadFile(dir+"/"+ name, size)

		data[name] = [date, hour, size]

		TCPConnection.TCPRead(1)
	return data
# -------------------------------- PROCESS FOR UDP --------------------------------
class UDPConnect:

	def __init__(self):
		try:
			self.UDPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)

			UDPPOpens.append(self)

			print(">> UDP server up and listening")
		except:
			print("error starting UDP")

	# FUNCTIONS TO COMMUNICATE

	def UDPReceive(self):
	
		bytesAddressPair = self.UDPClientSocket.recvfrom(BUFFERSIZE)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Recieved: ", message)
		return (message.split(), addrstruct)
	
		print("error receiving UDP")

	def UDPSend(self, message, addrstruct):
		try:
			bytesToSend = str.encode(message)
			self.UDPClientSocket.sendto(bytesToSend, addrstruct)
			print(">> Sent: ", message)
		except:
			print("error sending UDP")

	def UDPClose(self):
		try:
			self.UDPClientSocket.close()
			print(">> UDP closed")
		except:
			print("error closing UDP")
		
	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def init(self):
		message = "REG " + socket.gethostbyname(socket.gethostname()) + " " + str(BSPort)
		self.UDPSend(message, CSAddrStruct)
		msg, addrstruct = self.UDPReceive()
        
	def registerNewUser(self,user,pw,addrstruct):
		saveDataInFile(pw,USERPASS_FILE(user))
		self.UDPSend("LUR OK", addrstruct)

	def listFilesFromUser(self,user,folder,addrstruct):
		print("cheguei")
		dir = USERFOLDER_PATH(user, folder)
		repInfo = getDataFromFile(dir + "/.~repoinfo_" +  folder + '.txt')
		print(repInfo)
		numberOfFiles = len(repInfo)
		msgLFD = "LFD " + str(numberOfFiles) 
		for filename in repInfo:
			msgLFD += " " + filename + " " + repInfo[filename][0] + " " + repInfo[filename][1] + " " + str(repInfo[filename][2])
		self.UDPSend(msgLFD,addrstruct)

	def deleteDir(self, user, folder, addrstruct):
		dir = USERFOLDER_PATH(user, folder)
		print(dir)
		if checkDirExists(dir):
			try:
				shutil.rmtree(dir)
				msgDBR = "DBR OK"
				self.UDPSend(msgDBR,addrstruct)
			except:
				msgDBR = "DBR NOK"
				self.UDPSend(msgDBR,addrstruct)
		dir = USERFOLDERS_PATH(user)
		if not os.listdir(dir):
			try:
				os.rmdir(dir)
				os.remove(USERPASS_FILE(user))
			except:
				msgDBR = "DBR NOK"
				self.UDPSend(msgDBR,addrstruct)



	def run(self):
		dictUDPFunctions = {
			"registerNewUser": self.registerNewUser,
			'listFilesFromUser': self.listFilesFromUser,
			"deleteDir": self.deleteDir
		}

		# --------------------------- MAIN ---------------------------
		self.init()
		i= 0
		# READ MESSAGES
		while 1:
			print("iter ", i)
			i+=1
			message, addrstruct = self.UDPReceive()

			command = message[0]
			print(command)
			if command == 'LSU':
				dictUDPFunctions["registerNewUser"](message[1], message[2], addrstruct)
			elif command == 'LSF':
				dictUDPFunctions["listFilesFromUser"](message[1], message[2], addrstruct)
			elif command == "DLB":
				dictUDPFunctions["deleteDir"](message[1], message[2], addrstruct)
			
		# CLOSE CONNECTIONS
		self.UDPClientSocket.close()

def UDPSIGINT(_, __):
	print("vou fechar")
	for udp in UDPPOpens:
		msgUNR = "UNR " + localIP + " " + str(BSPort)
		udp.UDPSend(msgUNR, CSAddrStruct)
		msg, addrstruct = udp.UDPReceive()
		
		if msg[1] == "OK":
			udp.UDPClose()
		elif msg[1] == "NOK":
			print("UAR NOK")
		else:
			print("UAR ERR")	
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
			print("error starting TCP socket")

	
	def startServer(self):
		try:
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
		except:
			print("error starting TCP server")
			sys.exit()
	
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPWrite(self, tosend):
		try:
			nleft = len(tosend)
			while (nleft):
				nleft -= self.connection.send(tosend)
		except:
			print("error writing TCP")

	def TCPWriteMessage(self, message): 
		bytesToSend = str.encode(message)
		self.TCPWrite(bytesToSend)
		print(">> Sent: ", message)
		

	def TCPRead(self, bufferSize):
		try:
			return self.connection.recv(bufferSize)
		except:
			print("error reading TCP")

	def TCPReadMessage(self):
		message = self.TCPReadStepByStep(BUFFERSIZE, '\n')
		print(">> Received: ", message)
		return message.split()

	def TCPReadWord(self):
		word = self.TCPReadStepByStep(1, ' ')
		print(">> Received Word: ", word)
		return word

	def TCPReadStepByStep(self, bufferSize, end):
		message = ""
		while (not len(message) or (len(message) and message[-1] != end)):
			message += bytes.decode(self.TCPRead(bufferSize))
		return message[:-1] #erase end from string

	def TCPReadFile(self, filename, filesize):
		try:
			os.makedirs(os.path.dirname(filename), exist_ok = True)
			with open(filename, "wb") as fp:
				while(filesize):
					if filesize > BUFFERSIZE:
						toRead = BUFFERSIZE
					else:
						toRead = filesize
					bytes = self.TCPRead(toRead)
					fp.write(bytes)
					filesize -= len(bytes)

			print('>> Received File: ', filename)
		except:
			print("error reading files from directory")


	def TCPWriteFile(self, filepath):
		try:
			fp = open(filepath, 'rb') #mode: read bytes
			data = fp.read(BUFFERSIZE)
			while (data):
				self.TCPWrite(data)
				data = fp.read(BUFFERSIZE)
			fp.close()
			print(">> Sent File: ", filepath)
		except:
			print("error writing file")

	def TCPClose(self):
	
		self.connection.close()
		self.TCPServerSocket.close()
		print(">> TCP closed")
	
		#print("error closing TCP")

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def TCPSIGINT(_, __):
	print("tcpsigint")
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
	folder = TCPConnection.TCPReadWord()
	dir = USERFOLDER_PATH(currentUser, folder)
	numberOfFiles = int(TCPConnection.TCPReadWord())
	data = receiveFileAndWrite(dir, numberOfFiles, TCPConnection)
	
	saveDataInFile(data, dir + "/.~repoinfo_" +  folder + '.txt')
	TCPConnection.TCPWriteMessage("UPR OK\n")
	

def restore(msg, socket):
	dir = USERFOLDER_PATH(currentUser,msg[1])
	print(dir)
	files = [name for name in os.listdir(dir)]
	fileInfos = []
	fileNames = []
	for f in files:
		fileInfos.append([f, time.strftime("%d.%m.%Y %H:%M:%S", time.gmtime(os.path.getmtime(dir + '/' + f))), os.path.getsize(dir + '/' + f)])
		fileNames.append(f)
	numberOfFiles = len(files)
	msgRBR = "RBR " + str(numberOfFiles)
	i = 0
	repoInfo = ".~repoinfo_" + msg[1] + ".txt"
	for info in fileInfos:
		if fileNames[i] == repoInfo: #dont send the repo info
			continue
		for data in info:
			print("data", data)
			msgRBR += " " + str(data)
		print("msgRBR ", msgRBR)
		socket.TCPWriteMessage(msgRBR + " ")
		print("fileNames[i]", fileNames[i])
		socket.TCPWriteFile(dir + "/" + fileNames[i])
		i += 1
		msgRBR = ""
	socket.TCPWriteMessage("\n")


# --------------------------- MAIN ---------------------------

dictTCPFunctions = {
	"authenticateUser": authenticateUser,
	"writeBS": writeBS,
	"restore": restore

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
			msg = [msgFromClient] + connection.TCPReadMessage()
			print("oi ", msg)
			dictTCPFunctions["authenticateUser"](msg, connection)
		elif command == "UPL":
			dictTCPFunctions["writeBS"](msgFromClient, connection)
		elif command == "RSB":
			msg = [msgFromClient] + connection.TCPReadMessage()
			print("restore ", msg)
			dictTCPFunctions["restore"](msg, connection)
		
	sys.exit()

else:
	signal.signal(signal.SIGINT, UDPSIGINT)
	UDPConnect().run()

	sys.exit()