'''
Created on Oct 12, 2016

@author: mwittie
'''
import queue
import threading

#test change
## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.queue = queue.Queue(maxsize);
        self.mtu = None
    
    ##get packet from the queue interface
    def get(self):
        try:
            return self.queue.get(False)
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, block=False):
        self.queue.put(pkt, block)
        
        
## Implements a network layer packet (different from the RDT packet 
# from programming assignment 2).
# NOTE: This class will need to be extended to for the packet to include
# the fields necessary for the completion of this assignment.
class NetworkPacket:
    ## packet encoding lengths
    packetIDLength = 2 #We are going to make it so you can have 99 individual packet IDs. Type is bytes  
    
    dst_addr_S_length = 5 #Length of the destination address in bytes
    lastPacketFlagLength = 1; #How long (in bytes) our last packet flag is.
    identifierLength = packetIDLength + dst_addr_S_length + lastPacketFlagLength
    ##@param dst_addr: address of the destination host
    # @param data_S: packet payload
    def __init__(self, dst_addr, packetID, endFlag, data_S):
        self.dst_addr = dst_addr
        self.packetID = packetID
        self.endFlag = endFlag
        self.data_S = data_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst_addr).zfill(self.dst_addr_S_length)
        byte_S += str(self.packetID).zfill(self.packetIDLength)
        byte_S += str(self.endFlag).zfill(self.lastPacketFlagLength)
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst_addr = int(byte_S[0 : NetworkPacket.dst_addr_S_length]) #This says the destination address is from 
        packetID = int(byte_S[NetworkPacket.dst_addr_S_length: (NetworkPacket.dst_addr_S_length + NetworkPacket.packetIDLength)]) #From the end of the address to the end of ID length.
        endFlag = int(byte_S[(NetworkPacket.dst_addr_S_length + NetworkPacket.packetIDLength) :((NetworkPacket.dst_addr_S_length + NetworkPacket.packetIDLength) + NetworkPacket.lastPacketFlagLength)])
        data_S = byte_S[((NetworkPacket.dst_addr_S_length + NetworkPacket.packetIDLength) + NetworkPacket.lastPacketFlagLength) : ] #The rest is data.
        return self(dst_addr,packetID, endFlag, data_S)
    

    def isTooLong(self,mtu):
        if(mtu - (self.identifierLength + len(self.data_S)) < 0):
            return True
        else:
            return False 

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.in_intf_L = [Interface()]
        self.out_intf_L = [Interface()]
        self.stop = False #for thread termination
        self.packetIDGen = 0 #Generates a packet ID.
    
    ## called when printing the object
    def __str__(self):
        return 'Host_%s' % (self.addr)
       
    ## create a packet and enqueue for transmission
    # @param dst_addr: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst_addr, data_S):
        
        packetList = [] #Creates a list of segmented packets to send
        p = NetworkPacket(dst_addr,self.packetIDGen, 1, data_S) # Our initial packet 
        self.segmentPacket(packetList, p, self.out_intf_L[0].mtu)#Split the packets up.
        for x in range(len(packetList)):      
            self.out_intf_L[0].put(packetList[x].to_byte_S()) #send packets always enqueued successfully
            print('%s: sending packet "%s" on the out interface with mtu=%d' % (self, packetList[x], self.out_intf_L[0].mtu))
        self.packetIDGen += 1
  
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.in_intf_L[0].get()
        reconstructionString = ''
        if pkt_S is not None: 
            p = NetworkPacket.from_byte_S(pkt_S)          
            print('%s: received packet "%s" on the in interface' % (self, pkt_S)) 
            reconstructionString += p.data_S
            while(p.endFlag != 1):
                pkt_S = None
                pkt_S = self.in_intf_L[0].get()
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S)   
                    reconstructionString += p.data_S
            print("Message: " + reconstructionString)        

    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        
    def segmentPacket(self, packetList,p,mtu): #This method keeps splitting packets down until we can send the entire message.
        if(p.isTooLong(mtu)):
            maxDataSize = (mtu-p.identifierLength)#Max size of data.
            filledMTU = NetworkPacket(p.dst_addr,p.packetID,0,p.data_S[0: maxDataSize])
            packetList.append(filledMTU)#Adds a max size packet into the packetList
            q = NetworkPacket(p.dst_addr,p.packetID,1,p.data_S[maxDataSize: ]) #Creates another packet to be checked for size.
            self.segmentPacket(packetList,q,mtu)#Recursivly checks size.
        else:
            packetList.append(p)
  

## Implements a multi-interface router described in class
class Router:
    
    ##@param name: friendly router name for debugging
    # @param intf_count: the number of input and output interfaces 
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, intf_count, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.in_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]
        self.out_intf_L = [Interface(max_queue_size) for _ in range(intf_count)]

    ## called when printing the object
    def __str__(self):
        return 'Router_%s' % (self.name)

    ## look through the content of incoming interfaces and forward to
    # appropriate outgoing interfaces
    def forward(self):
        for i in range(len(self.in_intf_L)):
            pkt_S = None
            try:
                #get packet from interface i
                pkt_S = self.in_intf_L[i].get()
                #if packet exists make a forwarding decision
                if pkt_S is not None:
                    p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                    # HERE you will need to implement a lookup into the 
                    # forwarding table to find the appropriate outgoing interface
                    # for now we assume the outgoing interface is also i
                    packetList = [] #Creates a list of segmented packets to send
                    self.segmentPacket(packetList, p, self.out_intf_L[0].mtu)#Split the packets up.
                    for x in range(len(packetList)):      
                        self.out_intf_L[i].put(packetList[x].to_byte_S(), True)
                        print('%s: forwarding packet "%s" from interface %d to %d with mtu %d' % (self, packetList[x], i, i, self.out_intf_L[i].mtu))
            except queue.Full:
                print('%s: packet "%s" lost on interface %d' % (self, p, i))
                pass
    def segmentPacket(self, packetList,p,mtu): #This method keeps splitting packets down until we can send the entire message.
        if(p.isTooLong(mtu) and p.endFlag == 0):
            maxDataSize = (mtu-p.identifierLength)#Max size of data.
            filledMTU = NetworkPacket(p.dst_addr,p.packetID,0,p.data_S[0: maxDataSize])
            packetList.append(filledMTU)#Adds a max size packet into the packetList
            q = NetworkPacket(p.dst_addr,p.packetID,0,p.data_S[maxDataSize: ]) #Creates another packet to be checked for size.
            self.segmentPacket(packetList,q,mtu)#Recursivly checks size.
        elif(p.isTooLong(mtu) and p.endFlag == 1):
            maxDataSize = (mtu-p.identifierLength)#Max size of data.
            filledMTU = NetworkPacket(p.dst_addr,p.packetID,0,p.data_S[0: maxDataSize])
            packetList.append(filledMTU)#Adds a max size packet into the packetList
            q = NetworkPacket(p.dst_addr,p.packetID,1,p.data_S[maxDataSize: ]) #Creates another packet to be checked for size.
            self.segmentPacket(packetList,q,mtu)#Recursivly checks size.            
        else:
            packetList.append(p)            
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.forward()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 