import socket
import sys
import json
import time
import threading
import random
import base64
from pathlib import Path
import stat
from Node import *

class Network():
    def __init__(self,topology, callback=None):
        super(Network, self).__init__()
        self.callback = callback
        self.graph = topology
        self.Nodes = []
        self.num_nodes = len(topology)
        self.create_nodes()
        
        
    def create_nodes(self):
        pass
        for n in self.graph :
            if(self.graph.index(n)==0):
                new_node = Node(n)
                new_node.debug = False
            else:
                new_node = Node(n)
                new_node.debug = False
            new_node.start()
            self.Nodes.append(new_node)
            
            
    def init_network(self):
        pass
        for n in self.Nodes :
            for neigh in n.neigh_id :
                neigh_list = [x for x in self.graph if x[0]==neigh]
                neigh_ip = neigh_list[0][1]
                neigh_port = neigh_list[0][2]
                neigh_delay = n.neigh_delay[n.neigh_id.index(neigh)]
                #neigh_ip = n.ip
                #neigh_port = n.port
                n.connect_with_node(neigh_ip,neigh_port,neigh,neigh_delay)
            
    def file_request(self,node_id,file_name):
        for n in self.Nodes :
            if(n.id == node_id):
                target_node = n
                break
        if(target_node != None):
            pass
            target_node.send_fileQuery(file_name)
        else:
            print("requested node not found")
    
    def delete_node(self,node_id):
        for n in self.Nodes :
            if(n.id == node_id):
                target_node = n
                break
        if(target_node != None):
            target_node.terminate_flag.set()
        else:
            print("requested node not found")
    
    def add_node(self, node_id ,ip, port, neigh_id,neigh_ip,neigh_port,neigh_delay,file_list):
        node_arg = [node_id, ip, port, neigh_id, neigh_delay, file_list]
        new_node = Node(node_arg)
        #new_node.debug = False
        new_node.start()
        for neigh in neigh_id :
            this_neigh_ip = neigh_ip[neigh_id.index(neigh)]
            this_neigh_port = neigh_port[neigh_id.index(neigh)]
            #neigh_ip = n.ip
            #neigh_port = n.port
            new_node.connect_with_node(this_neigh_ip,this_neigh_port,neigh)
        self.Nodes.append(new_node)
            
    
    def add_file(self,node_id,file_name):
        target_node = None
        for n in self.Nodes :
            if(n.id == node_id):
                target_node = n
                break
        if(target_node != None):
            pass
            target_node.file_list.append(file_name)
        else:
            print("requested node not found")
    def remove_file(self,node_id,file_name):
        target_node = None
        for n in self.Nodes :
            if(n.id == node_id):
                target_node = n
                break
        if(target_node != None):
            del target_node.file_list[target_node.file_list.index(file_name)]
        else:
            print("requested node not found")
    def close_net(self):
        for n in self.Nodes :
            n.terminate_flag.set()
