# Chat-Application
A client server based chat which uses UDP Transport Layer Protocol

...Tested on Ubuntu 20.04...

To ensure reliabiltiy, I have implemented checksums, and ack packet. The next packet is only sent when the ack packet for the previous packet is received. If an ack packet is not received within a certian time, the packet is resent. This is repeated thrice after which the packet is dropped

Ack packets are the acknowledgement that the a packet has been received by the end user/server

### Files required to run:
- client.py  
- server.py  
- util.py  

## Server.py  
Server.py is the server for this chat application. All requests by client are forwared to server which responds back to the client depending on the request  
The server can handle 10 cients at a time and do so by using threading. Server displays all the exchanges between user and server
To run server `python server.py`
  
## Client.py
Client.py handles the client end of the chat applicaton. 
To run client `python client.py -u USERNAME` 
where USERNAME will be the user. Usernames need to be unique to avoid any conflict
  
##  Functionality Implemented:
- requesting list of users
- broadcast message to 1 or more users
- file sharing to 1 more users
- quit app

##  Format:
Available Users: `list`
Message: `msg <number_of_users> <username1> <username2> … <message>`
File Sharing: `file <number_of_users> <username1> <username2> … <file_name>`
Quit: `quit`
