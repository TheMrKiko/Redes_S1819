import socket



msgFromServer       = "Hello TCP Client\n"

bytesToSend         = str.encode(msgFromServer)

serverAddressPort   = ("127.0.0.1", 58002)

bufferSize          = 1024



# Create a TCP socket at client side

TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

TCPServerSocket.bind(serverAddressPort)

TCPServerSocket.listen(1)

conection , addr = TCPServerSocket.accept()
print("Client: ", addr)

msgFromClient = ""
while (msgFromClient[-1] != '\n'):
	msgFromClient += bytes.decode(conection.recv(bufferSize))


# Send to server using created UDP socket
nleft = len(bytesToSend)
while (nleft):
	nleft -= conection.send(bytesToSend)






msg = "Message from Client {}".format(msgFromClient[0])
conection.close()
TCPServerSocket.close()
print(msg)
