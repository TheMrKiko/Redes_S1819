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
	print("dir ", dir)
	data = {}

	for i in range(numberOfFiles):
		name = TCPConnection.TCPReadWord()
		print("name ", name)
		date = TCPConnection.TCPReadWord()
		print("date",date)
		hour = TCPConnection.TCPReadWord()
		print("hour",hour)
		size = int(TCPConnection.TCPReadWord())
		print("size", size)
		print(name, date, hour, int(size))

		TCPConnection.TCPReadFile(dir+"/"+ name, size)

		data[name] = [date, hour, size]

		TCPConnection.TCPRead(1)
	return data

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:

	def __init__(self):
		try:
			self.TCPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
		except:
			print("error creating TCP socket")

	def startClient(self, addrstruct):
		try:
			self.TCPClientSocket.connect(addrstruct)
			print(">> Client connected to ", addrstruct)
			return self
		except:
			print("error connecting to server ", addrstruct)
			
	
	# ------------------- FUNCTIONS TO COMMUNICATE -------------------
	def TCPWrite(self, tosend):
		nleft = len(tosend)
		while (nleft):
			try:
				nleft -= self.TCPClientSocket.send(tosend)
			except:
				print("error sending ", self)

	def TCPWriteMessage(self, message): #PUT \n in the end pls
		try:
			bytesToSend = str.encode(message)
			self.TCPWrite(bytesToSend)
			print(">> Sent: ", message)
		except:
			print("error sending message ", self)

	def TCPWriteFile(self, filepath):
		try:
			fp = open(filepath, 'rb') #mode: read bytes
		except:
			print("error opening file ", filepath)
		data = fp.read(BUFFERSIZE)
		while (data):
			self.TCPWrite(data)
			data = fp.read(BUFFERSIZE)
		try:
			fp.close()
		except:
			print("error closing file ", filepath)
		print(">> Sent File: ", filepath)

	def TCPRead(self, bufferSize):
		try:
			result = self.TCPClientSocket.recv(bufferSize)
			return result
		except:
			print("error receiving TCP")

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
		except:
			print("os error making dirs ", filename)
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
		try:
			self.TCPClientSocket.close()
			print(">> TCP closed")
		except:
			print("error closing TCP socket")

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def loginUser(credentials, socket):
		print(credentials)
		message = "AUT" + " " + credentials[0] + " " + credentials[1] + "\n"
		print(message.split())
		socket.TCPWriteMessage(message)
		word = socket.TCPReadMessage()
		print(word)
		return word
	
def checkUserCredentials():
	global userCredentials
	print(userCredentials)
	if len(userCredentials) != 0:
		return "OK"
	else:
		return "not logged in"

def login(msgFromClient, socket):
	global userCredentials
	if checkUserCredentials() == "not logged in":
		if len(msgFromClient) == 2:
			user = msgFromClient[0]
			pw = msgFromClient[1]
			if (user.isdigit() and pw.isalnum() and len(user) == 5 and len(pw) == 8):
				msg = loginUser([user, pw], socket)
				if msg[0] == "ERR" or msg[1] == "NOK":
					print("authentication error")
				else:
					userCredentials = [user, pw]
			else:
				print("please enter a valid user and password")
	else:
		print("logout first")
	socket.TCPClose()
		
def logout():
	global userCredentials
	userCredentials = []
	print("logout successful")

def deluser(socket):
	global userCredentials
	checkCredentials = checkUserCredentials()
	if checkCredentials == "OK":
		loginreply = loginUser(userCredentials, socket)
		if loginreply[0] == "ERR":
			print("ERR authentication")
		elif loginreply[1] == "OK":
			socket.TCPWriteMessage("DLU\n")
			msgDLR = socket.TCPReadMessage()

			if msgDLR[0] == "ERR":
				print("ERR deluser")
			elif msgDLR[1] == "OK":
				print("deleted user " + userCredentials[0])
			elif msgDLR[1] == "NOK":
				print("error: user not deleted")
				print("error: erase backup dirs first")
	else:
		print("deluser: " + checkCredentials)
	socket.TCPClose()

def dirlist(socket):
	global userCredentials
	checkCredentials = checkUserCredentials()
	if checkCredentials == "OK":
		loginreply = loginUser(userCredentials, socket)
		if loginreply[0] == "ERR":
			print("ERR authentication")
		elif loginreply[1] == "OK":
			socket.TCPWriteMessage("LSD\n")
			msgFromCS = socket.TCPReadMessage()
			print(msgFromCS)
			if msgFromCS == ["LSD", "0"]:
				print(msgFromCS)
			elif msgFromCS[0] == "ERR":
				print("ERR")
			else:
				numberOfDirs = int(msgFromCS[1])
				for i in range(numberOfDirs):
					print(msgFromCS[2+i])
	else:
		print("dirlist: " + checkCredentials)
	socket.TCPClose()

def filelist(folder,socket):
	global userCredentials
	checkCredentials = checkUserCredentials()
	if checkCredentials == "OK":
		loginreply = loginUser(userCredentials, socket)
		if loginreply[0] == "ERR":
			print("ERR authentication")
		elif loginreply[1] == "OK":
			socket.TCPWriteMessage("LSF " + folder + "\n")
			msgLFD = socket.TCPReadMessage()
	else:
		print("filelist + " + folder + ": " + checkCredentials)
	socket.TCPClose()

def deleteDir(folder,socket):
	global userCredentials
	checkCredentials = checkUserCredentials()
	if checkCredentials == "OK":
		loginreply = loginUser(userCredentials, socket)
		if loginreply[0] == "ERR":
			print("ERR authentication")
		elif loginreply[1] == "OK":
			socket.TCPWriteMessage("DEL " + folder + '\n')
			msgDDR = socket.TCPReadMessage()
			if msgDDR[1] == "OK":
				print(folder + " deleted")
	else:
		print("deletedir + " + folder + ": " + checkCredentials)
	socket.TCPClose()

def backup(folder, socket):
	checkCredentials = checkUserCredentials()
	if checkCredentials == "OK":
		loginreply = loginUser(userCredentials, socket)
		print(loginreply)
		if loginreply[0] == "ERR":
			print("ERR authentication")
		elif loginreply[1] == "OK":
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
	else:
		print("backup + " + folder + ": " + checkCredentials)
	socket.TCPClose()

def restore(folder,socket):
	checkCredentials = checkUserCredentials()
	if checkCredentials == "OK":
		loginreply = loginUser(userCredentials, socket)
		if loginreply[0] == "ERR":
			print("ERR authentication")
		elif loginreply[1] == "OK":
			socket.TCPWriteMessage("RST " + folder + "\n")
			msgRSR = socket.TCPReadMessage()
			print(msgRSR)
			if msgRSR[1] != "EOF":
				BSAddrStruct = (msgRSR[1], int(msgRSR[2]))
				print(BSAddrStruct)

				socket2 = TCPConnect().startClient(BSAddrStruct)
				socket2.TCPWriteMessage("AUT " + userCredentials[0] + ' ' + userCredentials[1] + "\n")
				
				msgFromBS = socket2.TCPReadMessage()
				if msgFromBS[1] == "OK":
					socket2.TCPWriteMessage("RSB " + folder + "\n")
					msgRBR = socket2.TCPReadWord()
					num = socket2.TCPReadWord()
					print(num)
					numberOfFiles = int(num)
					receiveFileAndWrite("./" + folder, numberOfFiles, socket2)
				else:
					print("RSB NOK")
				socket2.TCPClose()
			else:
				print("restore error")
	else:
		print("backup + " + folder + ": " + checkCredentials)
	socket.TCPClose()

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
	

#login("86450", "joanachicabarata", TCPClientSocket)
#backup("RC")

while not close:
	TCPClientSocket = TCPConnect().startClient(CSAddrStruct)
	request = input().split()
	command = request[0]
	if command == "login":
		dictFunctions["login"](request[1:], TCPClientSocket)
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