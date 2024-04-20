import socket
import threading
import json
import time
class SeedNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.peer_list = []
    
    def write_output(self,data):
        with open("output.txt",'a') as file:
            file.write(f"{self.ip}:{self.port}:-  {str(data)}  \n")

    def handle_registration(self, client_socket, client_address):
        print(f"Received REGISTER message from peer node...127.0.0.1\n")
        peer_info = client_socket.recv(1024).decode()
        print("Received peer info:", peer_info)
        peer_info = json.loads(peer_info)
        self.write_output(peer_info)
        self.peer_list.append(peer_info)
        print(f"Registered peer: {peer_info}")
        print(f"Peer List {self.peer_list}")
        client_socket.close()


    def handle_peer_list_request(self, client_socket, client_address,peer_to_send):
        print(f"Received PEER_LIST request from peer node... {client_address}")
        peer_list_json = json.dumps(peer_to_send)
        client_socket.send(peer_list_json.encode())
        print(f"Sent the PEER LIST to the {client_address} \n")
        client_socket.close()

    def handle_dead_node(self, client_socket, client_address):
        dead_node_info = client_socket.recv(1024).decode('utf-8')
        dead_node_info = json.loads(dead_node_info)

        print(f"Received dead node message: {dead_node_info} from {client_address}\n")
        if dead_node_info in self.peer_list:
            self.peer_list.remove(dead_node_info)
            print(f"Removed dead node: {dead_node_info}")
        client_socket.close()

    def start(self):

#<________________________CODE TO CONNECT TO PORTS AVAILABLE IN SEEDS.TXT FILE________________>

        
        # Setting up the seed node socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.ip, self.port))
        server_socket.listen()
        time.sleep(1.25)
        print(f"Seed node started at {self.ip}:{self.port}")

        with open("config.txt", "a") as file:
            file.write(str(self.port)+"\n")

        while True:
            # Accept client connections
            client_socket, client_address = server_socket.accept()
            request_type = client_socket.recv(1024).decode()
            
            print("\n")
    # ----------- HANDLE REQUESTS FOR REGISTRATION OF NODES 
            if request_type == "REGISTER":
                # print(1)
                self.write_output(request_type)
                self.handle_registration(client_socket,client_address)
                # threading.Thread(target=self.handle_registration, args=(client_socket, client_address)).start()
        # ----------- HANDLE REQUESTS TO GET PEER LISTS 
            elif request_type == "PEER_LIST":
                ip,port = client_address
                peer_to_send = []
                # print(ip + " " + port + "\n")
                for peer in self.peer_list:
                    if peer != {"ip":ip,"port":port - 3}:
                        peer_to_send.append(peer)
                self.handle_peer_list_request(client_socket,client_address,peer_to_send)

                # threading.Thread(target=self.handle_peer_list_request, args=(client_socket, client_address,peer_to_send)).start()
    # ----------- HANDLE REQUESTS FOR DEAD NODES
            elif request_type == "DEAD_NODE":
                self.handle_dead_node(client_socket,client_address)
                # threading.Thread(target=self.handle_dead_node, args=(client_socket, client_address)).start()

          

if __name__ == "__main__":
    port = int(input())
    seed_node = SeedNode("127.0.0.1", port)
    seed_node.port = port
    seed_node.start() #<--- LINE 26