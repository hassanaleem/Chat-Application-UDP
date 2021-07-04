# Chat-Application
A client server based chat which uses UDP Transport Layer Protocol

To ensure reliabiltiy, I have implemented checksums, and ack packet. The next packet is only sent when the ack packet for the previous packet is received.

---
Ack packets are the acknowledgement that the a packet has been received by the end user/server
---

### Files required to run:
- client.py  
- server.py  
- util.py  

## Server.py  
Server.py is the server for this chat application. All requests by client are forwared to server which responds back to the client depending on the request  
The server can handle 10 cients at a time and do so by using threading  
To run server `python server.py`
  
## Client.py
Client.py handles the client end of the chat applicaton. 
To run client `python client.py -u USERNAME` 
where USERNAME will be the user
  
##  Functionality Implemented:
- broadcast message to 1 or more users
- file sharing to 1 more users


 
