'''
This module defines the behaviour of a client in your Chat Application
'''
import sys
import getopt
import socket
import random
from threading import Thread
import os
import util
from queue import Queue

queue = Queue()
ack_queue = Queue()
'''
Write your code inside this class. 
In the start() function, you will read user-input and act accordingly.
receive_handler() function is running another thread and you have to listen 
for incoming messages in this function.
'''


class Client:
    '''
    This is the main Client Class. 
    '''
    def __init__(self, username, dest, port, window_size):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(None)
        self.sock.bind(('', random.randint(10000, 40000)))
        self.name = username
        self.window = window_size
        self.sequence_number = 0
        self.sequence_number_recv = 0
    #helper function to print help details  
    def help(self):
        print("Formats:")
        print("Message: msg <number_of_users> <username1> <username2> … <message>")
        print("Available Users: list")
        print("File Sharing: file <number_of_users> <username1> <username2> … <file_name>")
        print("Quit: quit")
        
    #this functions manages when the user wants to disconnect from the server
    def quit(self):
        message = util.make_message("disconnect", 1, self.name)
        self.start_packet()        
        self.data_packet(message)
        self.end_packet()
       
        print("quitting")
        sys.exit(0)
        
    # Packet sent to start a connection  
    def start_packet(self):
        self.sequence_number = random.randint(1, 999)
        transmissions = 0    
            
        # Send a packet and if ack is not received then retransmit packet
        while(transmissions <= util.NUM_OF_RETRANSMISSIONS):
            try:
                start_packet = util.make_packet("start",self.sequence_number)
                self.sock.sendto(start_packet.encode("utf-8"), (self.server_addr, self.server_port))
                _ = ack_queue.get(timeout=util.TIME_OUT)
                break
            except:
                transmissions += 1
        
    #packet to indicate the connection has come to an end
    def end_packet(self):
        transmissions = 0  
        while(transmissions <= util.NUM_OF_RETRANSMISSIONS):
            try:
                end_packet = util.make_packet("end", self.sequence_number)
                self.sock.sendto(end_packet.encode("utf-8"), (self.server_addr, self.server_port))
                _ = ack_queue.get(timeout=util.TIME_OUT)
                break
            except:
                transmissions += 1
    
    # This functions sends the join message     
    def join(self):
        
        message = util.make_message("join", 1, self.name)
        size = util.CHUNK_SIZE
        chunks = [message[i:i+size] for i in range(0, len(message), size)]
        size = len(chunks)

        i = 0
        transmissions = 0
        while(transmissions <= util.NUM_OF_RETRANSMISSIONS):
            try:
                data_packet = util.make_packet("data", self.sequence_number , chunks[i])
                self.sock.sendto(data_packet.encode("utf-8"), (self.server_addr, self.server_port))
                _ = ack_queue.get(timeout=util.TIME_OUT)
                i += 1
                if(i == size):
                    break
            except:
                transmissions += 1
    
    #this function sends the actual message          
    def data_packet(self, message):
        size = util.CHUNK_SIZE
        chunks = [message[i:i+size] for i in range(0, len(message), size)]
        size = len(chunks)

        i = 0
        transmissions = 0
        while(transmissions <= util.NUM_OF_RETRANSMISSIONS):
            try:
                data_packet = util.make_packet("data", self.sequence_number , chunks[i])
                self.sock.sendto(data_packet.encode("utf-8"), (self.server_addr, self.server_port))
                seqno_rev = ack_queue.get(timeout=util.TIME_OUT)
                i += 1
                if(i == size):
                    break
            except:
                transmissions += 1
        

    def start(self):
        '''
        Main Loop is here
        Start by sending the server a JOIN message.
        Waits for userinput and then process it
        '''
        self.start_packet()
        self.join()
        self.end_packet()
        
        while True:
            message_input = input()
            details = message_input.split()
            if details[0] == "list":
                self.start_packet()
                message = util.make_message("request_user_list", 2)
                self.data_packet(message)
                self.end_packet()
                
            elif details[0] == "msg":
                message = ""
                for i in range(1, len(details), 1):
                    message += " " + details[i]
                
                message = util.make_message("send_message", 4, message)
                self.start_packet()
                self.data_packet(message)
                self.end_packet()
                    
            elif details[0] == "quit":
                self.quit()                
                break
                
            elif details[0] == "help":
                self.help()
                
            elif details[0] == "file":
                number_of_user = int(details[1])
                file_data = open(details[2+number_of_user], "r")
                file_data = file_data.read()
                msg = ""
                for i in range(1, len(details), 1):
                    if i == 1:
                        msg += details[i]
                    else:
                        msg += " " + details[i]
                             
                msg += " " + file_data
                message = util.make_message("send_file", 4, msg)
               
                self.start_packet()
                self.data_packet(message)
                self.end_packet()

            else:
                print("incorrect userinput format")
        
        raise NotImplementedError
            
    def receive_handler(self):
        '''
        Waits for a message from server and process it accordingly
        '''
        while True:
            msg, a = self.sock.recvfrom(4096)
            msg_type, seq_no, message, checksum = util.parse_packet(msg.decode("utf-8"))
                        
            if(msg_type == "start" or msg_type == "data" or msg_type == "end"):
                # if(util.validate_checksum(message)):
                ack_packet = util.make_packet("ack", int(seq_no)+1,)
                self.sock.sendto(ack_packet.encode("utf-8"), (self.server_addr, self.server_port))
            
            if(msg_type == "ack"):
                self.sequence_number_recv = int(seq_no)
                ack_queue.put(int(seq_no))                
                
            elif(msg_type == "data"):
                mylist = list(queue.queue)
                if((message in mylist) != 1):
                    queue.put(message)
                
            elif(msg_type == "end"):
                message = ""
                
                while(queue.empty() != 1):
                    message += queue.get()

                check = message.split()
                self.operations(check)

        raise NotImplementedError
    
    #this function handles all the user operations
    def operations(self, check):
        if(len(check)):
            if check[0] == "forward_message":
                display = ""
                for i in range(2, len(check)):
                    if i == 2:
                        display += check[i]
                    else:
                        display += " " + check[i]         
                print(display)
                
            elif check[0] == "forward_file":
                    
                display = ""
                for i in range(2, 5):
                    if i == 2:
                        display += check[i]
                    else:
                        display += " " + check[i] 

                print(display)
                message = ""
                new_filename = self.name + "_" + check[4]
                
                for i in range(5, len(check)):
                    if i == 5:
                        message +=  check[i]
                    else:
                        message += " " + check[i]
                file = open(new_filename, "w")
                file.write(message)
                file.close()
            
            elif check[0] == "response_user_list":
                display = ""
                for i in range(2, len(check)):
                    if i == 2:
                        display += check[i]
                    else:
                        display += " " + check[i] 
                        
                print(display)
                
            elif check[0] == "err_server_full":
                print("disconnected: server full")
                sys.exit(0)
                    
            elif check[0] == "err_username_unavailable":
                print("disconnected: username not available")
                sys.exit(0)
                    
            elif check[0] == "err_unknown_message":
                print("disconnected: server received an unknown command")
                sys.exit(0)



# Do not change this part of code
if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our Client module completion
        '''
        print("Client")
        print("-u username | --user=username The username of Client")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW_SIZE | --window=WINDOW_SIZE The window_size, defaults to 3")
        print("-h | --help Print this help")
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "u:p:a:w", ["user=", "port=", "address=","window="])
    except getopt.error:
        helper()
        exit(1)

    PORT = 15000
    DEST = "localhost"
    USER_NAME = None
    WINDOW_SIZE = 3
    for o, a in OPTS:
        if o in ("-u", "--user="):
            USER_NAME = a
        elif o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW_SIZE = a

    if USER_NAME is None:
        print("Missing Username.")
        helper()
        exit(1)

    S = Client(USER_NAME, DEST, PORT, WINDOW_SIZE)
    try:
        # Start receiving Messages
        T = Thread(target=S.receive_handler)
        T.daemon = True
        T.start()
        # Start Client
        S.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
