import socket
import sys
import os
import time

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
CSName = sys.argv[2]
close = False

if len(sys.argv) < 5:
	CSPort = 58013
else:
	CSPort = int(sys.argv[4])

CSAddrStruct  = (socket.gethostbyname(CSName), CSPort)
bufferSize = 1024
userCredentials = []

TCPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
TCPClientSocket.connect(CSAddrStruct)

print(">> Client connected to CS")

# FUNCTIONS TO COMMUNICATE IN TCP
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

def TCPClose(socket):
	socket.close()
	print(">> TCP closed")

# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
def loginUser(credentials):
	message = "AUT" + " " + credentials[0] + " " + credentials[1] + "\n"
	TCPWrite(message, TCPClientSocket)
	return TCPRead(TCPClientSocket)

def login(user, pw):
	msg = loginUser([user, pw])
	if (msg[1] == "OK" or msg[1] == "NEW"):
		global userCredentials
		userCredentials = [user, pw]

def backup(folder):
	loginreply = loginUser(userCredentials)
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
		TCPWrite(msg + "\n", TCPClientSocket)
		msgFromCS = TCPRead(TCPClientSocket)
		TCPClose(TCPClientSocket)

		TCPClientSocket2 = socket.socket(family = socket.AF_INET, type = socket.SOCK_STREAM)
		BSAddrStruct = (msgFromCS[1],int(msgFromCS[2]))
		TCPClientSocket2.connect(BSAddrStruct)

		TCPWrite("AUT " + userCredentials[0] + ' ' + userCredentials[1] + "\n",TCPClientSocket2)
		msgFromBS = TCPRead(TCPClientSocket2)
		#if msgFromBS[1] == "OK":



# --------------------------- MAIN ---------------------------
dictFunctions = {
	"login": login,
	"backup": backup
	}
	
login("123", "abc")
#backup("RC")
while not close:
	request = input().split()
	command = request[0]
	if command == "login":
		dictFunctions["login"](request[1], request[2])
	elif command == "backup":
		dictFunctions["backup"](request[1])
	elif command == "exit":
		close = True
		TCPClose(TCPClientSocket)