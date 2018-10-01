import socket
import sys


#msgFromClient       = "Hello TCP Server\n"

#bytesToSend         = str.encode(msgFromClient)


csServer = sys.argv[2]
csPort = sys.argv[4]
if csPort is None:
	csPort = 58013
else:
	csPort = int(csPort)

serverAddressPort   = (csServer, csPort)

bufferSize          = 1024

# Create a TCP socket at client side

TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
TCPClientSocket.connect(serverAddressPort)


request = input();
while request != "exit":
    #print(request)
    request = request.split(" ")
    command = request[0]
    if command == "login":
        user = request[1]
        pw = request[2]
        message = "AUT" + " " + user + " " + pw + "\n"
        print(message[:-1])
        bytesToSend = str.encode(message)


        # Send to server using created UDP socket
        nleft = len(bytesToSend)
        while (nleft):
	           nleft -= TCPClientSocket.send(bytesToSend)


        msgFromServer = " "
        while (msgFromServer[-1] != '\n'):
	           msgFromServer += bytes.decode(TCPClientSocket.recv(bufferSize))
        msgFromServer = msgFromServer[1:-1] #erase space and \n from string


        msg = "Message from Server {}".format(msgFromServer)


        print(msg)
        print(list(msgFromServer))
        request = input()
TCPClientSocket.close()
