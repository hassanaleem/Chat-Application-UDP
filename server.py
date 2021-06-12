'''
This module defines the behaviour of server in your Chat Application
'''
import sys
import getopt
import socket
import util
from queue import Queue
import threading
import random


MAX_USERS = util.MAX_NUM_CLIENTS
user_names = {}
user_address = {}
ack_queue = Queue()

message_chunks = {}


class Server:
    '''
    This is the main Server Class. You will to write Server code inside this class.
    '''
    def __init__(self, dest, port, window):
        self.server_addr = dest
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.server_addr, self.server_port))
        self.window = window
        self.sequence_number = 0
        self.sequence_number_recv = 0
    
    #Packet sent to start a connection
    def start_packet(self, addr):
        self.sequence_number = random.randint(1, 999)
        transmissions = 0
        
        #Send a packet and if ack is not received then retransmit packet
        while(transmissions < util.NUM_OF_RETRANSMISSIONS):
            try:
                start_packet = util.make_packet("start",self.sequence_number)
                self.sock.sendto(start_packet.encode("utf-8"), addr)
                _ = ack_queue.get(timeout=util.TIME_OUT)
                break
            except:
                transmissions += 1
        
    #packet to indicate the connection has come to an end
    def end_packet(self, addr):
        transmissions = 0
        while(transmissions < util.NUM_OF_RETRANSMISSIONS):
            try:
                end_packet = util.make_packet("end", self.sequence_number)
                self.sock.sendto(end_packet.encode("utf-8"), addr)
                _ = ack_queue.get(timeout=util.TIME_OUT)
                break
            except:
                transmissions += 1
                     
    def data_packet(self, message, addr):
        size = util.CHUNK_SIZE
        chunks = [message[i:i+size] for i in range(0, len(message), size)]
        size = len(chunks)

        #transmit all the chunks. retransmit a chunk if ack not received
        i = 0   
        transmissions = 0
        while(transmissions < util.NUM_OF_RETRANSMISSIONS):
            try:
                data_packet = util.make_packet("data",self.sequence_number,chunks[i])
                self.sock.sendto(data_packet.encode("utf-8"), addr)
                _ = ack_queue.get(timeout=util.TIME_OUT)
                i += 1
                if(i == size):
                    break
            except:
                transmissions += 1

    #join chunks to a message to evaluate what is inside the chunks
    def join_chunks(self, addr):
        queue = message_chunks[addr]
        message = ""
        i = 0
        while True:
            i += 1        
            temp = queue.get()
            if(temp == "end"):
                break
            else:
                message += temp

        msg_details = message.split()
        return msg_details
    
    #function to handle the threading
    def handle_user_thread(self, addr):

        while(True):
            msg_details = self.join_chunks(addr)
            self.operation(msg_details, addr)
             
    #function that handles all the operations
    def operation(self, msg_details, addr):
        if(len(msg_details)):
            if msg_details[0] == "join":
                self.join(msg_details[2], addr)
                        
            elif msg_details[0] == "request_user_list":
                list_user = []
                for x, names in user_names.items():
                    list_user.append(names)
                
                list_user.sort()
                user_list = "list:"
                for names in list_user:
                    user_list += " " + names
                    
                user_message = util.make_message("response_user_list", 3, user_list)

                self.start_packet(addr)
                self.data_packet(user_message, addr)
                self.end_packet(addr)
                
                print("request_users_list:", user_names[addr])
            
            elif msg_details[0] == "send_message":
                user_message = "msg: " + user_names[addr] + ":"
                
                no_of_people = int(msg_details[2])
                for i in range(3+no_of_people, len(msg_details), 1):
                    user_message += " " + msg_details[i]
                    
                i = 0 
                user_message = util.make_message("forward_message", 4, user_message)
                while(i < no_of_people):
                    if self.user_exists(msg_details[3+i]): 
                        self.start_packet(user_address[msg_details[3+i]])
                        self.data_packet(user_message, user_address[msg_details[3+i]])
                        self.end_packet(user_address[msg_details[3+i]])
                    else:
                        print("msg:", user_names[addr] , "to non-existent user", msg_details[3+i])
                    i += 1
                    
                print("msg:", user_names[addr])
                
            elif msg_details[0] == "disconnect":
                print("disconnected:", msg_details[2])
                _ = user_address.pop(msg_details[2])
                _ = user_names.pop(addr)
                
                              
            elif msg_details[0] == "send_file":
                
                
                no_of_people = int(msg_details[2])
                message = "file:" + " " + user_names[addr] + ":" + " " + msg_details[3+no_of_people]
                
                for i in range(4+no_of_people, len(msg_details)):
                    message += " " + msg_details[i] 
                message = util.make_message("forward_file", 4, message)
                
                i=0
                print("file:", user_names[addr])
                while(i < no_of_people):
                    if self.user_exists(msg_details[3+i]):
                        
                        self.start_packet(user_address[msg_details[3+i]])
                        self.data_packet(message, user_address[msg_details[3+i]])
                        self.end_packet(user_address[msg_details[3+i]])
                                                
                    else:
                        print("file:", user_names[addr], "to non-existent user", msg_details[3+i])
                    i += 1
            
            else:             
                message = util.make_message("err_unknown_message", 2)
                self.start_packet(addr)
                self.data_packet(message, addr)
                self.end_packet(addr)
                
                print("disconnected:", user_names[addr], "incorrect userinput format")
                
    
    def start(self):
        '''
        Main loop.
        continue receiving messages from Clients and processing it
        '''
        while True:           
            message, addr = self.sock.recvfrom(10240)
            msg_type, seq_no, message, checksum = util.parse_packet(message.decode("utf-8"))
            if(msg_type == "start" or msg_type =="data" or msg_type =="end"):
                # if(util.validate_checksum(message)):
                ack_packet = util.make_packet("ack", int(seq_no)+1,)
                self.sock.sendto(ack_packet.encode("utf-8"), addr)
                            
            if(msg_type == "ack"):
                self.sequence_number_recv = int(seq_no)
                ack_queue.put(int(seq_no))
                    
            if(msg_type == "data"):
                if(len(message.split()) > 0 and message.split()[0] == "join"):
                    queue = Queue()
                    message_chunks[addr] = queue
                    threading.Thread(target=self.handle_user_thread, args=(addr,)).start()
                     
                queue = message_chunks[addr]
                mylist = list(queue.queue)
                if((message in mylist) != 1):
                    queue.put(message)
                    
                message_chunks[addr] = queue
                                    
            if(msg_type == "end"):
                queue = message_chunks[addr]
                mylist = list(queue.queue)
                temp = "end"
                if((temp in mylist) != 1):
                    queue.put("end")
                
                message_chunks[addr] = queue
            
                
           
        raise NotImplementedError      
    
    #Handles the joining of the user
    def join(self, user, addr):
        if self.user_exists(user):
            message = util.make_message("err_username_unavailable", 2)
            self.start_packet(addr)
            self.data_packet(message, addr)
            self.end_packet(addr) 
        
        else:
            if len(user_names) <= MAX_USERS:
                user_names[addr] = user
                user_address[user] = addr
                print("join:", user)
                
            elif len(user_names) > MAX_USERS:
                message = util.make_message("err_server_full", 2)
                self.start_packet(addr)
                self.data_packet(message, addr)
                self.end_packet(addr)     
                
    #helper function to see if the user already exists   
                     
    def user_exists(self, user):
        if user in user_address.keys():
            return True
        else:
            return False
            
            
            
    



# Do not change this part of code

if __name__ == "__main__":
    def helper():
        '''
        This function is just for the sake of our module completion
        '''
        print("Server")
        print("-p PORT | --port=PORT The server port, defaults to 15000")
        print("-a ADDRESS | --address=ADDRESS The server ip or hostname, defaults to localhost")
        print("-w WINDOW | --window=WINDOW The window size, default is 3")
        print("-h | --help Print this help")

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:],
                                   "p:a:w", ["port=", "address=","window="])
    except getopt.GetoptError:
        helper()
        exit()

    PORT = 15000
    DEST = "localhost"
    WINDOW = 3

    for o, a in OPTS:
        if o in ("-p", "--port="):
            PORT = int(a)
        elif o in ("-a", "--address="):
            DEST = a
        elif o in ("-w", "--window="):
            WINDOW = a

    SERVER = Server(DEST, PORT,WINDOW)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
