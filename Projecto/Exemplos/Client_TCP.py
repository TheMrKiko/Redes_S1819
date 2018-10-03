import socket

 

msgFromClient       = "Hello TCP Server\n"

bytesToSend         = str.encode(msgFromClient)

serverAddressPort   = ("192.168.1.1", 58070)

bufferSize          = 1024

 

# Create a TCP socket at client side

TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)

TCPClientSocket.connect(serverAddressPort)

# Send to server using created UDP socket
nleft = len(bytesToSend)
while (nleft):
	nleft -= TCPClientSocket.send(bytesToSend)

 
msgFromServer = " " 
while (msgFromServer[-1] != '\n'):
	msgFromServer += bytes.decode(TCPClientSocket.recv(bufferSize))

 

msg = "Message from Server {}".format(msgFromServer[0])
TCPClientSocket.close()

print(msg)