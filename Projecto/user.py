import socket
import sys


#msgFromClient       = "Hello TCP Server\n"

#bytesToSend         = str.encode(msgFromClient)


csServer = sys.argv[2]

if len(sys.argv) < 5:
	csPort = 58013
else:
	csPort = int(sys.argv[4])

serverAddressPort   = (csServer, csPort)

bufferSize          = 1024

# Create a TCP socket at client side

TCPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
TCPClientSocket.connect(serverAddressPort)

"""def func():
	print("pilinha")

dict = {"f":func}
dict["f"]()"""
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
