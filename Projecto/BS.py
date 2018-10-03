import socket
import sys
import os
import signal

# ------------------------ VARS, CONSTANTS AND ARGS ------------------------
BSPort = sys.argv[2]
CSName = sys.argv[4]

if len(sys.argv) < 7:
	CSPort = 58013
else:
	CSPort = int(sys.argv[6])

CSAddrStruct = (socket.gethostbyname(CSName), CSPort)
bufferSize  = 1024

# -------------------------------- PROCESS FOR UDP --------------------------------
def UDPConnect():

	UDPClientSocket = socket.socket(family = socket.AF_INET, type = socket.SOCK_DGRAM)

	# FUNCTIONS TO COMMUNICATE
	def UDPReceive(socket):
		bytesAddressPair = socket.recvfrom(bufferSize)
		message = bytes.decode(bytesAddressPair[0])
		addrstruct = bytesAddressPair[1]
		print(">> Recieved: ", message)
		return (message.split(), addrstruct)
	
	def UDPSend(message, socket, addrstruct):
		bytesToSend = str.encode(message)
		socket.sendto(bytesToSend, addrstruct)
		print(">> Sent: ", message)

	def UDPClose(socket):
		socket.close()
		print(">> UDP closed")
	
	def UDPSIGINT(_, __):
		UDPClose(UDPClientSocket)
		sys.exit()
	
	signal.signal(signal.SIGINT, UDPSIGINT)

	# ------------------- FUNCTIONS TO MANAGE COMMANDS -------------------
	def init():
		message = "REG " + socket.gethostbyname(socket.gethostname()) + " " + str(BSPort)
		UDPSend(message, UDPClientSocket, CSAddrStruct)
		msg, addrstruct = UDPReceive(UDPClientSocket)

	# --------------------------- MAIN ---------------------------
	init()

	# READ MESSAGES
	#while 1:
		
	# CLOSE CONNECTIONS
	UDPClientSocket.close()


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
	TCPConnect()
	sys.exit()
else:
	UDPConnect()
	sys.exit()