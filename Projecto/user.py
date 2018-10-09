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

# -------------------------------- PROCESS FOR TCP --------------------------------
class TCPConnect:

	def __init__(self):
		self.TCPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)

	def startClient(self, addrstruct):
		self.TCPClientSocket.connect(CSAddrStruct)

		print(">> Client connected to CS")

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

	def TCPClose(self):
		self.TCPClientSocket.close()
		print(">> TCP closed")

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def loginUser(credentials, socket):
	message = "AUT" + " " + credentials[0] + " " + credentials[1] + "\n"
	socket.TCPWriteMessage(message)
	return socket.TCPReadMessage()

def login(user, pw, socket):
	msg = loginUser([user, pw], socket)
	if (msg[1] == "OK" or msg[1] == "NEW"):
		global userCredentials
		userCredentials = [user, pw]

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
		socket.TCPClose()

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
			


# --------------------------- MAIN ---------------------------
dictFunctions = {
	"login": login,
	"backup": backup
	}
	
TCPClientSocket = TCPConnect().startClient(CSAddrStruct)

login("123", "abc", TCPClientSocket)
#backup("RC")

while not close:
	request = input().split()
	command = request[0]
	if command == "login":
		dictFunctions["login"](request[1], request[2], TCPClientSocket)
	elif command == "backup":
		dictFunctions["backup"](request[1], TCPClientSocket)
	elif command == "exit":
		close = True
		TCPClientSocket.TCPClose()