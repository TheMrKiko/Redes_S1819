#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#define PORT 58000
#include <stdio.h>
#include <string.h>

int fd;
struct hostent *hostptr;
struct sockaddr_in serveraddr, clientaddr;
int addrlen;
char msg[80], buffer[80];

int main(int argc, char const *argv[])
{
	if ((fd = socket(AF_INET, SOCK_DGRAM,0)) == -1){
		return 1;
	}

	memset((void*)&serveraddr, (int)'\0', sizeof(serveraddr));
	serveraddr.sin_family = AF_INET;
	serveraddr.sin_addr.s_addr = htonl(INADDR_ANY);
	serveraddr.sin_port = htons((u_short)PORT);
	if((bind(fd,(struct sockaddr*)&serveraddr,sizeof(serveraddr)))== -1){
		return 2;
	}
	addrlen=sizeof(clientaddr);
	if(recvfrom(fd,buffer,sizeof(buffer),0,(struct sockaddr*)&clientaddr,&addrlen)==-1){
		return 3;
	}
	printf("%s\n", buffer);
	if(sendto(fd,"TU e que es\n",strlen("TU e que es\n"),0,(struct sockaddr*)&clientaddr,addrlen)==-1){
		return 4;
	}
	if(close(fd)){
		return 5;
	}
	return 0;
}