import socket
import sys

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
CSName = sys.argv[2]

if len(sys.argv) < 5:
	CSPort = 58013
else:
	CSPort = int(sys.argv[4])

CSAddrStruct  = (socket.gethostbyname(CSName), CSPort)
bufferSize = 1024

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
def login(user, pw):
	message = "AUT" + " " + user + " " + pw + "\n"
	TCPWrite(message, TCPClientSocket)
	msg = TCPRead(TCPClientSocket)
	
# --------------------------- MAIN ---------------------------
dictFunctions = {
	"login": login
	}

while 1:
	request = input().split()
	command = request[0]
	if command == "login":
		dictFunctions["login"](request[1], request[2])
	elif command == "exit":
		TCPClose(TCPClientSocket)