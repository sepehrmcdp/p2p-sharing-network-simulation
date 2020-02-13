
class Node(threading.Thread):

    def __init__(self,node_args, callback=None):
        super(Node, self).__init__()

        # This flag is used for closing the node
        self.terminate_flag = threading.Event()

        # Server details, host (or ip) to bind to and the port
        self.id = node_args[0]
        self.ip = node_args[1]
        self.port = int(node_args[2])

        # Events are send back to the given callback
        self.callback = callback

        # Nodes that have established a connection with this node
        self.neigh_id = node_args[3]  
        #self.neigh_ip = neigh_ip_list 
        #self.neigh_port = neigh_port_list 
        self.neigh_delay = node_args[4]  
        self.file_list = node_args[5]
        # Nodes that this nodes is connected to
        #self.connectedNodes = [] 
        # Incoming connections
        self.nodesIn = []  
        # Outgoing connections , must match the incoming ones
        self.nodesOut = []  # Nodes that we are connected to (US)->N
        # Start the server
        self.init_server()

        self.queries_sent = []
        self.queries_answered = []
        self.message_count_send = 0;
        self.message_count_recv = 0;

        self.files_receiving = []
        # Debugging prints information about everything on console
        self.debug = False

        self.default_ttl = 5
        
        self.path = "N" + str(self.id)+"/"
        Path(self.path).mkdir(mode=stat.S_IWRITE,parents=True, exist_ok=True)

    def get_message_count_send(self):
        return self.message_count_send

    def get_message_count_recv(self):
        return self.message_count_recv

    
    def enable_debug(self):
        self.debug = True

    def dprint(self, message):
        if ( self.debug ):
            print("Node "+str(self.id)+" DPRINT: " + message)

    # Creates the TCP/IP socket and bind is to the ip and port
    def init_server(self):
        print("Initialisation of the TcpServer on port: " + str(self.port) + " on node (" + str(self.id) + ")")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.bind((self.host, self.port))
        self.sock.bind(('', self.port))
        self.sock.settimeout(10.0)
        self.sock.listen(1)

    def print_connections(self):
        self.dprint("Connection status:")
        self.dprint("- Total nodes connected with us: %d" % len(self.nodesIn))
        self.dprint("- Total nodes connected to     : %d" % len(self.nodesOut))
        #self.dprint("- Total nodes connected: %d" % len(self.neigh_id))
        
    def get_inbound_nodes(self):
        pass
        return self.nodesIn

    def get_outbound_nodes(self):
        pass
        return self.nodesOut

    def get_id(self):
        return self.id

    def get_host(self):
        return self.ip

    def get_port(self):
        return self.port

    # Check if a connection is closed(other node exit the network) so delete the connection
    def delete_closed_connections(self):
        for n in self.nodesIn:
            if n.terminate_flag.is_set():
                self.event_node_inbound_closed(n)

                self.dprint( str(self.id)+" NODEINBOUNDCLOSED: (" + str(n.id) +")" )

                
                n.join()
                del self.nodesIn[self.nodesIn.index(n)]

        for n in self.nodesOut:
            if n.terminate_flag.is_set():
                self.event_node_outbound_closed(n)

                self.dprint( str(self.id)+" NODEOUTBOUNDCLOSED: (" + str(n.id) +")" )

                
                n.join()
                del self.nodesOut[self.nodesOut.index(n)]
    ###### message: { '_sender_id','_timestamp','_path_id','_type','_main_data'}
    def create_message(self, data):
                        
        data['_sender_id']  = self.get_id()
        if('_timestamp' not in data):
            data['_timestamp']  = time.time()
        if('_path_id' not in data):
            data['_path_id'] = [self.get_id()]
        
        return data;

    # Send a message to all the nodes that are connected with this node.
    # data uses JSON format
    def send_to_nodes(self, data, exclude = []):
        for n in self.nodesIn:
            if n in exclude:
                self.dprint("TcpServer.send2nodes: Excluding node in sending the message")
            else:
                self.send_to_node(n, data)

        for n in self.nodesOut:
            if n in exclude:
                self.dprint("TcpServer.send2nodes: Excluding node in sending the message")
            else:
                self.send_to_node(n, data)

    def send_out_to_nodes(self, data, exclude = []):
        
        for n in self.nodesOut:
            if n in exclude:
                self.dprint("TcpServer.send2nodes: Excluding node in sending the message")
            else:
                self.send_to_node(n, data)

    
    # Send the data to the node n if it exists.
    # data is a python variabele which is converted to JSON that is send over to the other node.
    def send_to_node(self, n, data):
        self.delete_closed_connections()
        if n in self.nodesIn or n in self.nodesOut:
            try:
                n.send(self.create_message( data ))
                
            except Exception as e:
                self.dprint("TcpServer.send2node: Error while sending data to the node (" + str(e) + ")");
        else:
            self.dprint("TcpServer.send2node: Could not send the data, node is not found!")

    # Make a connection with another node.
    def connect_with_node(self, host, port, dest_id=None,delay=0.1):
        print("connect_with_node(" + host + ", " + str(port) + ")")
        if ( host == self.ip and port == self.port ):
            print("connect_with_node: It is the same node!")
            return;

        # Check if node is already connected with this node!
        for node in self.nodesOut:
            if ( node.get_host() == host and node.get_port() == port ):
                print("connect_with_node: Already connected with this node.")
                return True
        #for node in self.nodesIn:
        #    if ( node.get_host() == host and node.get_port() == port ):
        #        print("connect_with_node: Already connected with this node.")
        #        return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.dprint("connecting to %s port %s" % (host, port))
            sock.connect((host, port))

            #thread_client = NodeConnection(self, sock, (host, port), self.callback)
            thread_client = self.create_new_connection(sock, (host, port), self.callback,delay)
            thread_client.start()
            if(dest_id != None):
                thread_client.id = dest_id
            self.send_hello(thread_client)
            self.nodesOut.append(thread_client)
            self.event_connected_with_node(thread_client)

            
            self.print_connections()

        except Exception as e:
            self.dprint("TcpServer.connect_with_node: Could not connect with node. (" + str(e) + ")")

    # Disconnect with a node.
    def disconnect_with_node(self, node):
        if node in self.nodesOut:
            node.stop()
            node.join() 
            del self.nodesOut[self.nodesOut.index(node)]

    # When this function is executed, the node will turn off
    def stop(self):
        self.terminate_flag.set()

    def create_new_connection(self, connection, client_address, callback, delay):
        return NodeConnection(self, connection, client_address, callback , delay)

    # This function implements the main loop of this thread. starts after start()
    def run(self):
        while not self.terminate_flag.is_set():  # this is for easy removing node
            ## checking the filerequests timeout , about every 10 seconds
            
            #####
            try:
                self.dprint("TcpServerNode: Wait for incoming connection")
                connection, client_address = self.sock.accept()

                thread_client = self.create_new_connection(connection, client_address, self.callback,delay=0)
                thread_client.start()
                self.nodesIn.append(thread_client)

                self.event_node_connected(thread_client)


                
            except socket.timeout:
                pass

            except:
                raise

            time.sleep(0.01)

        print("TcpServer stopping...")
        for t in self.nodesIn:
            t.stop()

        for t in self.nodesOut:
            t.stop()

        time.sleep(1)

        for t in self.nodesIn:
            t.join()

        for t in self.nodesOut:
            t.join()

        self.sock.close()
        print("TcpServer stopped")

        
    
    # node is the connection thread
    def event_node_connected(self, node):
        self.dprint("event_node_connected: " + node.getName())
        
    def event_connected_with_node(self, node):
        self.dprint("event_node_connected: " + node.getName())

    def event_node_inbound_closed(self, node):
        self.dprint("event_node_inbound_closed: " + node.getName())

    def event_node_outbound_closed(self, node):
        self.dprint("event_node_outbound_closed: " + node.getName())
        
    
    #######################################################
    # PING / PONG Message packet                          #
    #######################################################

    # A ping request is sent to all the nodes that are connected
    def send_ping(self):
        self.send_out_to_nodes(self.create_message( {'_type': 'ping', '_timestamp': time.time(), '_sender_id': self.get_id()} ))

    # A pong request is sent as answer to node that sent ping
    def send_pong(self, node, timestamp):
        node.send(self.create_message( {'_type': 'pong', '_timestamp': timestamp, '_timestamp_node': time.time(), '_sender_id': self.get_id()} ))

    # answer ping with ppong
    def received_ping(self, node, data):
        self.send_pong(node, data['_timestamp'])

    # Pong received - connection is alive
    def received_pong(self, node, data):
        latency = time.time() - data['_timestamp']

        
    #######################################################
    # HELLO Message packet                          #
    #######################################################
    def received_hello(self, node, data):
        node.id = data['_sender_id']
        has_con = False
        for n in self.nodesOut :
            if n.id == data['_sender_id']:
                has_con = True
        if(has_con == False):
            self.connect_with_node(data['_sender_ip'],data['_sender_port'],data['_sender_id'],data['_link_delay'])
            
            
    
    def send_hello(self, node):
        node.send(self.create_message( {'_type': 'hello', '_timestamp': time.time(), '_sender_id': self.get_id(),
                                       '_sender_ip':self.ip ,'_sender_port':self.port,'_link_delay':node.delay } ))
            
    ########################################################
    # receiving messages
    ########################################################
    def event_node_message(self, node, data):
        
        if('_type' in data):
            if (data['_type'] == 'ping'):
                self.dprint("received_ping: " + ": " + str(data))
                print("Node " + str(self.id) + "  received_ping: " + ": " + str(data))
                self.received_ping(node, data)
                
            elif (data['_type'] == 'pong'):
                self.dprint("received_pong: "+ ": " + str(data))
                print("Node " + str(self.id) + "  received_pong: " + ": " + str(data))
                
                self.received_pong(node, data)

            elif (data['_type'] == 'hello'):
                self.dprint("received_hello: "+ ": " + str(data))
                print("Node " + str(self.id) + "  received_hello: " + ": " + str(data))
                
                self.received_hello(node, data)
            elif (data['_type'] == 'fileQuery'):
                self.dprint("received_fileQuery: "+ ": " + str(data))
                print("Node " + str(self.id) + "  received_fileQuery: " + ": " + str(data))
                
                self.received_fileQuery(node, data)
            elif (data['_type'] == 'fileFound'):
                self.dprint("received_fileFound: "+ ": " + str(data))
                print("Node " + str(self.id) + "  received_fileFound: " + ": " + str(data))
                
                self.received_fileFound(node, data)
            
            elif (data['_type'] == 'Fail'):
                self.dprint("received_Fail: "+ ": " + str(data))
                print("Node " + str(self.id) + "  received_Fail: " + ": " + str(data))
                
                self.received_Fail(node, data)
            
            elif (data['_type'] == 'FGET'):
                self.dprint("received_FGET: "+ ": " + str(data))
                print("Node " + str(self.id) + "  received_FGET: " + ": " + str(data))
                
                self.received_FGET(node, data)
            elif (data['_type'] == 'FileContain'):
                #self.dprint("received_FileContain: "+ ": " + str(data))
                self.dprint("received_FileContain")
                self.received_FileContain(node, data)

            else:
                self.dprint("p2p_event_node_message: message type unknown: " + node.getName() + ": " + str(data))
        else:
            self.dprint("event_node_message: " + node.getName() + ": " + str(data))

            
    #######################################################
    # FileQuery                                           #
    #######################################################

         
    def send_fileQuery(self,filename='default.txt'):
        data = {'_type': 'fileQuery','_qid':len(self.queries_sent) , '_timestamp': time.time(), '_sender_id': self.get_id(),
                                                    '_main_data': filename , '_ttl': self.default_ttl}
        self.queries_sent.append(data)
        self.send_out_to_nodes(self.create_message( data ))
        
        
    
    def received_fileQuery(self, node, data):
        rec_path = data['_path_id']
        if self.id in rec_path:
            self.dprint( "fileQuery: (" + str(data['_main_data']) +")" + "already received, discarding." )

        else:
            rec_path.append(self.id)
            if(data['_main_data'] in self.file_list ):
                self.dprint("fileQuery: (" + str(data['_main_data']) +")" + "I have the file.")
                #self.queries_answered.append(data)
                ###### message: { '_sender_id','_timestamp','_path_id','_type','_main_data'}
                #fileFound_ans = data
                fileFound_ans = {'_type': 'fileFound','_qid': data['_qid'], '_path_id':rec_path, '_generation_timestamp': data['_timestamp'] ,
                                 '_main_data':data['_main_data']}
                self.send_fileFound(node,fileFound_ans)
                
            else:
                if(int(data['_ttl'])>0):
                    data['_ttl'] = int(data['_ttl'])-1
                    self.dprint("fileQuery: (" + str(data['_main_data']) +")" + "data not found, forwarding.")
                    #rec_path.append(self.id)
                    data['_path_id']= rec_path
                    self.send_out_to_nodes(self.create_message( data ))
                else:
                    self.dprint("fileQuery: (" + str(data['_main_data']) +")" + "ttl expired, discarding.")
                    
                    
        
    def send_fileFound(self,node,data):
        node.send(self.create_message( data ))
        self.queries_answered.append(data)
    
    def received_fileFound(self, node, data):
        rec_path = data['_path_id']
        if (self.id != rec_path[0]): ## not for this user,must forward
            self.dprint( "fileFound: (" + str(data['_main_data']) +")" + "forwarding." )
            my_place = rec_path.index(self.id)
            next_node = rec_path[my_place-1]
            next_con = None
            for n in self.nodesOut :
                if n.id == next_node :
                    next_con = n
            if(next_con != None):
                next_con.send(self.create_message(data))
            else:
                self.dprint( "fileFound: (" + str(data['_main_data']) +")" + "ERROR forwarding" )
            

        else:
            self.dprint( "fileFound: (" + str(data['_main_data']) +")" + "recieved by client!." )
            ## first search all sent queries and find the one, then check the timestamp
            rec_qid = data['_qid']
            cor_query = None
            for qs in self.queries_sent :
                if(qs['_qid']==rec_qid and qs['_main_data']==data['_main_data']):
                    cor_query = qs
                    break
            if(cor_query != None):
                if(time.time()- data['_generation_timestamp'] > 10 ):
                    self.dprint( "fileFound: (" + str(data['_main_data']) +")" + "query was timed out" )
                    node.send(self.create_message({'_type': 'Fail', '_path_id':rec_path,
                                                   '_qid':data['_qid'],
                                                     '_main_data':data['_main_data']}))  #send the fail message
                    del self.queries_sent[self.queries_sent.index(qs)]
                    
                else:
                    self.dprint( "fileFound: (" + str(data['_main_data']) +")" + "sending FGET" )
                    
                    node.send(self.create_message({'_type': 'FGET', '_path_id':rec_path,
                                                   '_qid':data['_qid'],
                                                     '_main_data':data['_main_data']}))  #send the FGET message
                    self.files_receiving.append(qs)
                    del self.queries_sent[self.queries_sent.index(qs)]
                    
                
            else:
                self.dprint( "fileFound: (" + str(data['_main_data']) +")" + "no queries for this" )
                node.send(self.create_message({'_type': 'Fail', '_path_id':rec_path,
                                                   '_qid':data['_qid'],
                                                     '_main_data':data['_main_data']}))  #send the fail message
                    
            
    def received_Fail(self, node, data):
        rec_path = data['_path_id']
        if (self.id != rec_path[len(rec_path)-1]): ## not for this user,must forward
            self.dprint( "Fail: (" + str(data['_main_data']) +")" + "forwarding." )
            my_place = rec_path.index(self.id)
            next_node = rec_path[my_place-1]
            next_con = None
            for n in self.nodesOut :
                if n.id == next_node :
                    next_con = n
            if(next_con != None):
                next_con.send(self.create_message(data))
            else:
                self.dprint( "Fail: (" + str(data['_main_data']) +")" + "ERROR forwarding" )
        else:
            self.dprint( "Fail: (" + str(data['_main_data']) +")" + "recieved by source!." )
            ## first search all sent answers and find the one, then check the timestamp
            rec_qid = data['_qid']
            cor_ans = None
            for qs in self.queries_answered :
                if(qs['_qid']==rec_qid and qs['_main_data']==data['_main_data']):
                    cor_ans = qs
                    break
            if(cor_ans != None):
                ## must expire the answer
                del self.queries_answered[self.queries_answered.index(qs)]
                    
            else:
                self.dprint( "Fail: (" + str(data['_main_data']) +")" + "answer already expired" )
    
    def received_FGET(self, node, data):
        rec_path = data['_path_id']
        if (self.id != rec_path[len(rec_path)-1]): ## not for this user,must forward
            self.dprint( "FGET: (" + str(data['_main_data']) +")" + "forwarding." )
            my_place = rec_path.index(self.id)
            next_node = rec_path[my_place+1]
            next_con = None
            for n in self.nodesOut :
                if n.id == next_node :
                    next_con = n
            if(next_con != None):
                next_con.send(self.create_message(data))
            else:
                self.dprint( "FGET: (" + str(data['_main_data']) +")" + "ERROR forwarding" )
        else:
            self.dprint( "FGET: (" + str(data['_main_data']) +")" + "recieved by source!." )
            ## first search all sent queries and find the one, then check the timestamp
            rec_qid = data['_qid']
            cor_ans = None
            for qs in self.queries_answered :
                if(qs['_qid']==rec_qid and qs['_main_data']==data['_main_data']):
                    cor_ans = qs
                    break
            if(cor_ans != None):
                self.send_file_raw(node,data)
                self.dprint( "FGET: (" + str(data['_main_data']) +")" + "Preparing file to send" )
                #self.files_receiving.append(qs)
                del self.queries_answered[self.queries_answered.index(qs)]
            else:
                self.dprint( "FGET: (" + str(data['_main_data']) +")" + "answer already expired" )
    

    
     #######################################################
    # Sending and receiving Files                                           #
    #######################################################
    def send_file_raw(self,node,info_data):
        filename = info_data['_main_data']
        try:
            read_path = self.path
            raw_reader = open(read_path + filename, "rb")
            file_ready = raw_reader.read()
            out_data = base64.b64encode(file_ready)
            out_string = out_data.decode('utf-8')
            raw_reader.close()
            self.dprint( "FileContain: (" + str(info_data['_main_data']) +")" + "sending file" )
            print("Node " + str(self.id) + "FileContain: (" + str(info_data['_main_data']) +")" + "sending file")
                
            node.send(self.create_message({'_type': 'FileContain', '_filename': filename, '_path_id':info_data['_path_id'],
                                                   '_qid':info_data['_qid'],
                                                     '_main_data':out_string}))  #send the file
        
        except Exception as e:
            self.dprint("Reading file: Unexpected error: " + str(e))
        
    def received_FileContain(self,node,data):
        rec_path = data['_path_id']
        byte_received = base64.b64decode(data['_main_data'])
        #self.dprint("fileContain: (" + str(byte_received) +")" + "is here")
        if (self.id != rec_path[0]): ## not for this user,must forward
            self.dprint( "fileContain: (" + str(data['_qid']) +")" + "forwarding." )
            my_place = rec_path.index(self.id)
            next_node = rec_path[my_place-1]
            next_con = None
            for n in self.nodesOut :
                if n.id == next_node :
                    next_con = n
            if(next_con != None):
                next_con.send(self.create_message(data))
            else:
                self.dprint( "fileContain: (" + str(data['_qid']) +")" + "ERROR forwarding" )
            
        else:
            rec_qid = data['_qid']
            cor_query = None
            for qs in self.files_receiving :
                if(qs['_qid']==rec_qid and qs['_main_data']==data['_filename']):
                    cor_query = qs
                    break
            if(cor_query != None):
                self.dprint("fileContain: (" + str(data['_qid'])  +")" + "received, saving.")
                print("Node " + str(self.id) + "fileContain: (" + str(data['_qid'])  +")" + "received, saving.")
            
                file_save = open(self.path +  data['_filename'],'wb')
                file_save.write(byte_received)
                file_save.close()
                self.file_list.append(data['_filename'])
                del self.files_receiving[self.files_receiving.index(qs)]
                    
            else:
                self.dprint( "fileContain: (" + str(data['_filename']) +")" + "no need for this, discarding." )
                node.send(self.create_message({'_type': 'Fail', '_path_id':rec_path,
                                                   '_qid':data['_qid'],
                                                     '_main_data':data['_main_data']}))  #send the fail message
            
            #self.dprint("fileContain: (" + str(data['_qid'])  +")" + "received, saving.")
            #file_save = open(self.path +  data['_filename'],'wb')
            #file_save.write(byte_received)
            #file_save.close()

