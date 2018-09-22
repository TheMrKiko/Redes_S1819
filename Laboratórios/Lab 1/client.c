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
	hostptr=gethostbyname("lima");
	memset((void*)&serveraddr, (int)'\0', sizeof(serveraddr));
	serveraddr.sin_family = AF_INET;
	serveraddr.sin_addr.s_addr = ((struct in_addr *)(hostptr->h_addr_list[0]))->s_addr;
	serveraddr.sin_port = htons((u_short)PORT);
	
	addrlen=sizeof(serveraddr);
	if(sendto(fd,"Es parvo\n",strlen("Es parvo\n"),0,(struct sockaddr*)&serveraddr,addrlen)==-1){
		return 4;
	}
	if(recvfrom(fd,buffer,sizeof(buffer),0,(struct sockaddr*)&serveraddr,&addrlen)==-1){
		return 3;
	}
	printf("%s\n", buffer);
	
	if(close(fd)){
		return 5;
	}
	return 0;
}