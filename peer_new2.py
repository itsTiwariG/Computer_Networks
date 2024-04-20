import socket
import threading
import json
import time
import random

LOCALHOST = "127.0.0.1"
class PeerNode:
    def __init__(self, ip, port, seed_nodes):
        self.ip = ip
        self.port = port
        self.seed_nodes = seed_nodes
        self.peer_list = []
        self.message_list = []
        self.unq_peer_list = []
        self.liveness_timeout = 13  # Timeout for liveness checks in seconds
        self.num_exceptions = {}
    
    def write_output(self,data):
        with open("output.txt",'a') as file:
            file.write(f"{self.ip}:{self.port}:-  {str(data)} \n")

    def register_with_seed(self, seed_ip, seed_port):
        try:
            seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # seed_socket.bind((LOCALHOST, peer_node.port + 4))
            seed_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            seed_socket.connect((seed_ip, seed_port))
            print("Sending REGISTER message to seed node...")
            seed_socket.send("REGISTER".encode())
            time.sleep(1)
            peer_info = json.dumps({"ip": self.ip, "port": self.port})
            print("Sending peer info:", peer_info)
            seed_socket.send(peer_info.encode())
            seed_socket.close()
        except Exception as e:
            print(f"Seed Node not active: {seed_ip},{seed_port}")

    def get_peers_from_seed(self, seed_ip, seed_port):
        try:
            seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            seed_socket.bind((LOCALHOST, peer_node.port + 3))
            seed_socket.connect((seed_ip, seed_port))
            
            seed_socket.send("PEER_LIST".encode())
            peer_list_data = seed_socket.recv(1024).decode()

            self.peer_list += json.loads(peer_list_data)

            for ele in self.peer_list:
                if ele not in self.unq_peer_list:
                    self.unq_peer_list.append(ele)

            self.write_output(peer_list_data)
            print(f"Peer list recieved from {seed_ip}:{seed_port}: {self.peer_list}")
            seed_socket.close()
        except Exception as e:
            print(f"Error getting peer list from seed node: {e}")

    def gossip_message(self):
        # Simulating gossip message generation
        message = str(time.time()) + ":" + str(LOCALHOST) + ":" + str(self.port) + ":" + "GOSSIP"
        # print(f"Gossip message generated: {message}")
        self.forward_gossip_message(message," "," ")
        # self.message_list.append(message)

    def send_gossip(self):
        for i in range(10):
            self.gossip_message()
            time.sleep(5)


    def send_liveness_request(self, peer_ip, peer_port):
        self.num_exceptions[peer_ip,peer_port] = 0
        while(True):
            try:
                liveness_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                liveness_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                liveness_socket.settimeout(self.liveness_timeout)
                #Bind to a port to ensure that consistancy of port usage
                liveness_socket.bind((LOCALHOST, peer_node.port + 2))

                liveness_socket.connect((peer_ip, peer_port))
                liveness_request = "LIVENESS_REQUEST:" + str(time.time()) + ":" + str(LOCALHOST) + ':' + f"{peer_port}"
                print(liveness_request)
                liveness_socket.send(liveness_request.encode())
                message = liveness_socket.recv(1024).decode()
                message_parts = message.split(":")
                message_type = message_parts[0]
                if message_type.upper() == "LIVENESS_REPLY":
                    print(f"Liveness reply received from {peer_ip}:{peer_port} \n")

                liveness_socket.close()
            except socket.timeout:
                print(f"Timeout: No response from {peer_ip}:{peer_port}")
                peer_tuples.remove((peer_ip,peer_port)) 
                self.report_dead_node(peer_ip, peer_port)
            except Exception as e:
                print(f"Error sending liveness request to {peer_ip}:{peer_port}: {e}")

                # Increment the count of exceptions
                self.num_exceptions[peer_ip, peer_port] += 1

                # If the count exceeds three, declare the peer as dead
                if self.num_exceptions[peer_ip, peer_port] > 2:
                    self.num_exceptions[peer_ip, peer_port] = 0
                    del self.num_exceptions[peer_ip, peer_port]
                    peer_tuples.remove((peer_ip,peer_port)) 
                    print(f"Peer {peer_ip}:{peer_port} declared as dead node.")

                    self.report_dead_node(peer_ip, peer_port)
                    return
                
            time.sleep(13)

    def forward_gossip_message(self, received_message,client_socket,client_address):

        if received_message not in self.message_list:
            self.write_output(f"{time.time()}: {client_address}: {received_message}")
            self.message_list.append(received_message)   
            print(f"GOSSIP MESSAGE: from {client_address} {received_message}")
            for peer_ip, peer_port in peer_tuples:     
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((peer_ip, int(peer_port)))
                    sock.send(received_message.encode('utf-8'))
                    sock.close()
                except:
                    continue

    def handle_connection(self,client_socket,client_address): 
        message = client_socket.recv(1024).decode()
        # print(message)
        # print("\n")
        message_parts = message.split(":")
        message_type = message_parts[0]
        # print(message_parts)
        # print("\n")
        # print(message_type.type())
        if str(message_type.upper()) == "CONNECTION_REQUEST":
            peer_port = int(message_parts[2])
            peer_tuples.append((LOCALHOST, peer_port))
            print(f"Connection accepted from ({LOCALHOST},{peer_port})")
            threading.Thread(target=self.send_liveness_request, args=(client_address[0], peer_port)).start()
        elif str(message_type.upper()) == "LIVENESS_REQUEST":
            self.handle_liveness_request(client_socket, client_address)
        elif "GOSSIP" in str(message_parts[3]):
            self.forward_gossip_message(message,client_socket,client_address)


    def handle_liveness_request(self, client_socket, client_address):

        try:
            print(f"Received LIVENESS_REQUEST message from peer node...{client_address}")
            # Responding to the liveness request
            liveness_reply = "Liveness_Reply" + ":" +LOCALHOST + ":" + LOCALHOST
            client_socket.send(liveness_reply.encode())
            print(f"Sent LIVENESS_REPLY to {client_address}")
        except Exception as e:
            print(f"Error handling liveness request from {client_address}: {e}")
        finally:
            client_socket.close()

    def report_dead_node(self, dead_ip, dead_port):
        for seed_ip, seed_port in self.seed_nodes:
            try:
                report_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                report_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                report_socket.bind((LOCALHOST, peer_node.port + 1))
                report_socket.connect((seed_ip, seed_port))
                report_socket.send("DEAD_NODE".encode())
                #***********************
                time.sleep(1)
                data = {'ip':dead_ip,'port':dead_port}
                dead_message = "Dead Node:" + f"{data}" + ":" + str(time.time()) + ":" + LOCALHOST
                print(dead_message)
                self.write_output(dead_message)
                report_socket.send(json.dumps(data).encode())
                ####
                report_socket.close()
                print(f"***** Reported dead node to seed: {dead_ip}:{dead_port} to: {seed_ip}:{seed_port}: ****")
            except Exception as e:
                print(f"Error reporting dead node to seed: {e}")

    def start(self):
        self.num_exceptions = {}
        for seed_ip, seed_port in self.seed_nodes:
            self.register_with_seed(seed_ip, seed_port)
            self.get_peers_from_seed(seed_ip, seed_port)

        print(f"Registered with seeds: {self.seed_nodes}")
        # print(f"Obtained peers: {self.peer_list}")
        global peer_tuples
        peer_tuples = [(peer['ip'], peer['port']) for peer in self.unq_peer_list]
        if len(self.unq_peer_list) > 4:
            peer_tuples = random.sample(peer_tuples, 4)

        print(f"Peers to connect: {peer_tuples}")

        for peer_ip, peer_port in peer_tuples:
            self.num_exceptions[peer_ip,peer_port] = 0
        
        for peer_ip, peer_port in peer_tuples:
            print(f"********* PEER IP {peer_ip} PEER Port {peer_port} *********\n")  
            message = "CONNECTION_REQUEST"+":"+str(LOCALHOST)+":"+str(self.port)
            connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connect_socket.connect((peer_ip,int(peer_port)))
            connect_socket.send(message.encode())


        for peer_ip, peer_port in peer_tuples:
            # print(f"********* PEER IP {peer_ip} PEER Port {peer_port} *********\n")  
            threading.Thread(target=self.send_liveness_request, args=(peer_ip, int(peer_port))).start()
            

if __name__ == "__main__":

#<________________________CODE TO EXTRACT N//2 + 1 RANDOM SEEDS FROM THE SEEDS.TXT FILE________________>
    seed_nodes = []
    seed_ip = "127.0.0.1"
    with open("config.txt", "r") as file:
        seed_ports = file.readlines()
        # select (n/2 + 1) random seeds from the list
        random.seed(42)  # seed for reproducibility
        num_seeds = len(seed_ports)
        num_random_seeds = num_seeds // 2 + 1
        random_seeds = random.sample(seed_ports, num_random_seeds)
        for seed in random_seeds:
            seed_port = int(seed.strip())
            seed_nodes.append((seed_ip, int(seed_port)))

#<________________________CODE TO CONNECT TO PORTS AVAILABLE IN PEERS.TXT FILE________________>
    


    port_inp = int(input())
    # with open("peers.txt", "a") as file:
    #     file.write(str(port_inp) + '\n')

    peer_node = PeerNode("127.0.0.1", port_inp, seed_nodes)
    peer_node.port = port_inp
    recieve_livelines_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    recieve_livelines_socket.bind((LOCALHOST, peer_node.port))
    recieve_livelines_socket.listen(3)
    time.sleep(0.1)
    peer_node.start()

    #Create liveliness socket to respond to other PEERS
        # calling server socket method

    #Start Gossiping
    threading.Thread(target=peer_node.send_gossip).start() #<--- LINE 38
    while True:
        client_socket , client_address = recieve_livelines_socket.accept()
        # peer_node.handle_connection(client_socket,client_address)
        threading.Thread(target= peer_node.handle_connection, args=(client_socket,client_address)).start()