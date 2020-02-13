# p2p-sharing-network-simulation

Simulation of decentralised peer to peer network.  
The network consists of independent users(Nodes). Each node is connected to number of neighbouring nodes. Nodes can request files from network which will be routed through neighbours until the file is found or request timeouts. All nodes are independent and new nodes can join network anytime.  
It is assumed that all nodes are trustable. Routings are done automatically and best route can change between two request according to network changes.  
The class Network runs several nodes on localhost on single machine for simulation of such network. Each node creates it's directory on system to store files. 
