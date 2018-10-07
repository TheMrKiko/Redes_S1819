import socket
import sys
import os
import signal
import json

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
BSPort = sys.argv[2]
CSName = sys.argv[4]

if len(sys.argv) < 7:
	CSPort = 58013
else:
	CSPort = int(sys.argv[6])

CSAddrStruct = (socket.gethostbyname(CSName), CSPort)
bufferSize  = 1024

BSDATA_PATH = './bsdata_' + BSPort
BACKUPLIST_FILE = BSDATA_PATH + '/backup.txt'
TMP_UDP_FILE = BSDATA_PATH + '/UDPtempmessage.txt'
USERPASS_FILE = lambda user : BSDATA_PATH + '/users/user_'+ user + '.txt'
USERFOLDERS_PATH = lambda user : BSDATA_PATH + '/user_' + user
USERFOLDER_PATH = lambda user, folder : USERFOLDERS_PATH(user) + '/' + folder

# -------------------------------- PROCESS FOR UDP --------------------------------
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
def TCPConnect():
	print("TCP TODO")
	# Sending a reply to client

# ------------------------ SEPERATION OF PROCESSES ------------------------
pid = os.fork()
if pid == -1:
	print("erro no fork")
elif not pid:
	#TCPConnect()
	sys.exit()
else:
	UDPConnect().run()
	sys.exit()