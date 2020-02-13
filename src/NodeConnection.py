            
# Class NodeConnection
# The connection that is made with other node. there are two of these between each pair of neighbors
# Messages are received and sent to parent for processing
# Messages could be sent to this node.
class NodeConnection(threading.Thread):

    # Python constructor
    def __init__(self, nodeServer, sock, clientAddress, callback=None, delay = 0.1):
        super(NodeConnection, self).__init__()

        self.host = clientAddress[0]
        self.port = clientAddress[1]
        self.nodeServer = nodeServer
        self.sock = sock
        self.clientAddress = clientAddress
        self.callback = callback
        self.terminate_flag = threading.Event()
        self.delay = delay
        # Variable for parsing the incoming json messages
        self.buffer = ""

        self.id = None
    
    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    # Send data to the node. data must be dictionary.
    # This data is converted into json and sent.
    def send(self, data):
        #data = self.create_message(data) # Call it yourself!!

        try:
            message = json.dumps(data, separators=(',', ':')) + "-TSN";
            time.sleep(self.delay) ## simulating the link delay
            self.sock.sendall(message.encode('utf-8'))

            # For visuals!
            #self.nodeServer.send_visuals("node-send", data)

        except Exception as e:
            self.nodeServer.dprint("NodeConnection.send: Unexpected error:" + str(sys.exc_info()[0]))
            self.terminate_flag.set()
    def check_message(self, data):
        return True

    def get_id(self):
        return self.id

    # Stop the node client. Please make sure you join the thread.
    def stop(self):
        self.terminate_flag.set()

    # This is the main loop of the node connection.
    def run(self):

        # Timeout, so the socket can be closed when it is dead!
        self.sock.settimeout(10.0)

        while not self.terminate_flag.is_set(): # Check whether the thread needs to be closed
            line = ""
            try:
                line = self.sock.recv(4096) # the line ends with -TSN\n
                #line = line.encode('utf-8');
                
                
            except socket.timeout:
                pass

            except Exception as e:
                self.terminate_flag.set()
                self.nodeServer.dprint("NodeConnection: Socket has been terminated (%s)" % line)
                print(e)
            if line != "":
                try:
                    self.buffer += str(line.decode('utf-8'))
                except:
                    print("NodeConnection: Decoding line error")

                # Get the messages
                index = self.buffer.find("-TSN")
                while ( index > 0 ):
                    message = self.buffer[0:index]
                    self.buffer = self.buffer[index+4::]

                    try:
                        data = json.loads(message)
                        
                    except Exception as e:
                        print("NodeConnection: Data could not be parsed (%s) (%s)" % (line, str(e)) )

                    if ( self.check_message(data) ):
                        self.nodeServer.message_count_recv = self.nodeServer.message_count_recv + 1
                        self.nodeServer.event_node_message(self, data)
                        
                        
                        

                    else:
                        self.nodeServer.dprint("-------------------------------------------")
                        self.nodeServer.dprint("Message is damaged and not correct:\nMESSAGE:")
                        self.nodeServer.dprint(message)
                        self.nodeServer.dprint("DATA:")
                        self.nodeServer.dprint(str(data))
                        self.nodeServer.dprint("-------------------------------------------")

                    index = self.buffer.find("-TSN")

            time.sleep(0.01)

        self.sock.settimeout(None)
        self.sock.close()
        self.nodeServer.dprint("NodeConnection: Stopped")


