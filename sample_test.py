from Node import *
from Network import *
from NodeConnection import *

import socket
import sys
import json
import time
import threading
import random
import base64
from pathlib import Path
import stat


sample_topology = [[1, 'localhost', 5001, [2,3], [0.1,0.1], []],
 [2,'localhost', 5002, [1], [0.1,0.1], ['file.txt','logo.png','some2.xlsx']],
 [3,'localhost', 5003, [1], [0.1], ['introspect.mp3']]]
MyNet = Network(sample_topology)



MyNet.init_network()
#MyNet.Nodes[2].send_ping()
#MyNet.file_request(3,'some2.xlsx')
#MyNet.add_node(4,'localhost', 5005, [1,3], ['localhost','localhost'],#[5001,5003],[0.1,0.2], ['file3.txt'])
#MyNet.add_file(1,'some4.xlsx')
#MyNet.file_request(4,'my_music.mp3')
