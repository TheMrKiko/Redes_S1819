import socket
import sys
import os
import time
import signal

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
CSName = sys.argv[2]
close = False

if len(sys.argv) < 5:
	CSPort = 58013
else:
	CSPort = int(sys.argv[4])

CSAddrStruct  = (socket.gethostbyname(CSName), CSPort)
BUFFERSIZE = 1024
userCredentials = []
TCPOpens = []

def receiveFileAndWrite(dir, numberOfFiles, TCPConnection):

	data = {}

	for i in range(numberOfFiles):
		name = TCPConnection.TCPReadWord()
		date = TCPConnection.TCPReadWord()
		hour = TCPConnection.TCPReadWord()
		size = int(TCPConnection.TCPReadWord())
		print(name, date, hour, size)

		TCPConnection.TCPReadFile(dir+"/"+ name, size)

		data[name] = [date, hour, size]

		TCPConnection.TCPRead(1)
	return data

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:

	def __init__(self):
		self.TCPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)

	def startClient(self, addrstruct):
		self.TCPClientSocket.connect(addrstruct)

		print(">> Client connected to ", addrstruct)

		return self
	
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPWrite(self, tosend):
		nleft = len(tosend)
		while (nleft):
			nleft -= self.TCPClientSocket.send(tosend)

	def TCPWriteMessage(self, message): #PUT \n in the end pls
		bytesToSend = str.encode(message)
		self.TCPWrite(bytesToSend)
		print(">> Sent: ", message)

	def TCPWriteFile(self, filepath):
		fp = open(filepath, 'rb') #mode: read bytes
		data = fp.read(BUFFERSIZE)
		while (data):
			self.TCPWrite(data)
			data = fp.read(BUFFERSIZE)
		fp.close()
		print(">> Sent File: ", filepath)

	def TCPRead(self, bufferSize):
		return self.TCPClientSocket.recv(bufferSize)

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


	def TCPClose(self):
		self.TCPClientSocket.close()
		print(">> TCP closed")

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def loginUser(credentials, socket):
		message = "AUT" + " " + credentials[0] + " " + credentials[1] + "\n"
		socket.TCPWriteMessage(message)
		return socket.TCPReadMessage()
	
def login(user, pw, socket):
	global userCredentials
	if userCredentials == []:
		msg = loginUser([user, pw], socket)
		if (msg[1] == "OK" or msg[1] == "NEW"):
			userCredentials = [user, pw]
	else:
		print("logout first")

def logout():
	global userCredentials
	userCredentials = []
def deluser(socket):
	socket.TCPWriteMessage("DLU\n")

	msgDLR = socket.TCPReadMessage()
	global userCredentials
	if msgDLR[1] == "OK":
		print("deleted user " + userCredentials[0])

def dirlist(socket):
	loginreply = loginUser(userCredentials, socket)
	if loginreply[1] == "OK":
		socket.TCPWriteMessage("LSD\n")
		msgFromCS = socket.TCPReadMessage()
		if msgFromCS[1] == "dirs":
			print(msgFromCS)
		else:
			numberOfDirs = int(msgFromCS[1])
			for i in range(numberOfDirs):
				print(msgFromCS[2+i])

def filelist(folder,socket):
	loginreply = loginUser(userCredentials, socket)
	if loginreply[1] == "OK":
		socket.TCPWriteMessage("LSF " + folder + "\n")
		msgLFD = socket.TCPReadMessage()

def deleteDir(folder,socket):
	socket.TCPWriteMessage("DEL " + folder + '\n')
	msgDDR = socket.TCPReadMessage()
	if msgDDR[1] == "OK":
		print(folder + " deleted")

def backup(folder, socket):
	loginreply = loginUser(userCredentials, socket)
	if loginreply[1] == "OK":
		dir = "./" + folder
		files = [name for name in os.listdir(dir)]
		fileInfos = []
		for f in files:
			fileInfos.append([f, time.strftime("%d.%m.%Y %H:%M:%S", time.gmtime(os.path.getmtime(dir + '/' + f))), os.path.getsize(dir + '/' + f)])
		numberOfFiles = len(files)
		msg = "BCK " + folder + " " + str(numberOfFiles)
		for info in fileInfos:
			for data in info:
				msg += " " + str(data)
		socket.TCPWriteMessage(msg + "\n")
		msgFromCS = socket.TCPReadMessage() #BKR
		#socket.TCPClose()

		BSAddrStruct = (msgFromCS[1], int(msgFromCS[2]))
		
		socket2 = TCPConnect().startClient(BSAddrStruct)
	

		socket2.TCPWriteMessage("AUT " + userCredentials[0] + ' ' + userCredentials[1] + "\n")
		msgFromBS = socket2.TCPReadMessage()
		if msgFromBS[1] == "OK":
			numberOfFiles = msgFromCS[3]
			msg = "UPL " + folder + " " + numberOfFiles 

			for i in range(int(numberOfFiles)):
				j = 4 + i * 4
				msg += " " + msgFromCS[j] + " " + msgFromCS[j+1] + " " + msgFromCS[j+2] + " " + msgFromCS[j+3] + " "
				socket2.TCPWriteMessage(msg)
				socket2.TCPWriteFile(dir + "/" + msgFromCS[j])
				msg = ""
			socket2.TCPWriteMessage("\n")	

			reply = socket2.TCPReadMessage() #UPR
			if reply[1] == 'OK':
				print(">> file backup completed  ", folder)
			else:
				print("UPR NOK ;(")
			socket2.TCPClose()
			
def restore(folder,socket):
	loginreply = loginUser(userCredentials, socket)
	if loginreply[1] == "OK":
		socket.TCPWriteMessage("RST " + folder + "\n")
		msgRSR = socket.TCPReadMessage()
		print(msgRSR)
		BSAddrStruct = (msgRSR[1], int(msgRSR[2]))
		print(BSAddrStruct)
		socket2 = TCPConnect().startClient(BSAddrStruct)
		socket2.TCPWriteMessage("AUT " + userCredentials[0] + ' ' + userCredentials[1] + "\n")
		msgFromBS = socket2.TCPReadMessage()
		if msgFromBS[1] == "OK":
			socket2.TCPWriteMessage("RSB " + folder + "\n")
			msgRBR = socket2.TCPReadWord()
			numberOfFiles = int(socket2.TCPReadWord())
			receiveFileAndWrite("./" + folder, numberOfFiles, socket2)
		else:
			print("RSB NOK")
		socket2.TCPClose()


# --------------------------- MAIN ---------------------------
dictFunctions = {
	"login": login,
	"backup": backup,
	"dirlist": dirlist,
	"restore": restore,
	"logout": logout,
	"deluser": deluser,
	"deleteDir": deleteDir,
	"filelist": filelist

	}
	
TCPClientSocket = TCPConnect().startClient(CSAddrStruct)

login("86450", "joanachicabarata", TCPClientSocket)
#backup("RC")

while not close:
	request = input().split()
	command = request[0]
	if command == "login":
		dictFunctions["login"](request[1], request[2], TCPClientSocket)
	elif command == "backup":
		dictFunctions["backup"](request[1], TCPClientSocket)
	elif command == "dirlist":
		dictFunctions["dirlist"](TCPClientSocket)
	elif command == "restore":
		dictFunctions["restore"](request[1],TCPClientSocket)
	elif command =="logout":
		dictFunctions["logout"]()
	elif command == "deluser":
		dictFunctions["deluser"](TCPClientSocket)
	elif command == "delete":
		dictFunctions["deleteDir"](request[1],TCPClientSocket)
	elif command == "filelist":
		dictFunctions["filelist"](request[1],TCPClientSocket)
	elif command == "exit":
		close = True
		TCPClientSocket.TCPClose()