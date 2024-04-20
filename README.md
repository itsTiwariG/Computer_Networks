Each peer must connect to at least b(n/2)c+1 seeds out of n available seeds. Note that  

n will vary for each instance of the peer-to-peer network and the config file should be changed accord-
ingly. Config file contains the details (IP Address:Port) of seeds. The definitions of ”seed”,”peer”  

etc. are given below. Each ”peer” in the network must be connected to a randomly chosen subset  
of other peers. The network must be connected, that is the graph of peers should be a connected  
graph. In order to bootstrap the whole process, the network should have more than one Seed node  
which has information (such as IP address and Port Numbers) about other peers in the network.  
Any new node first connects to seed nodes to get information about other peers, and then connects  
to a subset of these.  
Once the network is formed, the peers broadcast messages in the network and keep checking the  
liveness of connected peers in regular intervals. If a node is found to be dead, the details of that  
node needs to be sent to the seeds.  
