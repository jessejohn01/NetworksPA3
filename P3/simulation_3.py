'''
Created on Oct 12, 2016

@author: mwittie
'''

from P3 import network_3 as network
from P3 import link_3 as link
import threading
from time import sleep

##configuration parameters
router_queue_size = 0 #0 means unlimited
simulation_time = 2 #give the network sufficient time to transfer all packets before quitting

if __name__ == '__main__':
    
    #Routing tables
    Ra_table = {3:2, 4:3}       
    Rb_table = {3:1}            
    Rc_table = {4:1}            
    Rd_table = {3:2, 4:3}       
    routing_table = {'Router_A': Ra_table, 'Router_B' : Rb_table,
                     'Router_C' : Rc_table, 'Router_D' : Rd_table}

    object_L = [] #keeps track of objects, so we can kill their threads

    #create network nodes
    host1 = network.Host(1)
    object_L.append(host1)

    host2 = network.Host(2)
    object_L.append(host2)

    host3 = network.Host(3)
    object_L.append(host3)

    host4 = network.Host(4)
    object_L.append(host4)

    router_a = network.Router(name='A', intf_count=4, max_queue_size=router_queue_size, routing_table=routing_table)
    object_L.append(router_a)

    router_b = network.Router(name='B', intf_count=2, max_queue_size=router_queue_size, routing_table=routing_table)
    object_L.append(router_b)

    router_c = network.Router(name='C', intf_count=2, max_queue_size=router_queue_size, routing_table=routing_table)
    object_L.append(router_c)

    router_d = network.Router(name='D', intf_count=4, max_queue_size=router_queue_size, routing_table=routing_table)
    object_L.append(router_d)

    #create a Link Layer to keep track of links between network nodes
    link_layer = link.LinkLayer()
    object_L.append(link_layer)

    #add all the links
    #link parameters: from_node, from_intf_num, to_node, to_intf_num, mtu
    #Host 1 outgoing links
    link_layer.add_link(link.Link(host1, 0, router_a, 0, 50))

    #Host 2 outgoing links
    link_layer.add_link(link.Link(host2, 0, router_a, 1, 50))

    #Router A outgoing links
    link_layer.add_link(link.Link(router_a, 2, router_b, 0, 50))
    link_layer.add_link(link.Link(router_a, 3, router_c, 0, 50))

    #Router B outgoing links
    link_layer.add_link(link.Link(router_b, 1, router_d, 0, 50))

    #Router C outgoing links
    link_layer.add_link(link.Link(router_c, 1, router_d, 1, 50))

    #Router D outgoing links
    link_layer.add_link(link.Link(router_d, 2, host3, 0, 50))
    link_layer.add_link(link.Link(router_d, 3, host4, 0, 50))

    #start all the objects
    thread_L = []

    #Host threads
    thread_L.append(threading.Thread(name=host1.__str__(), target=host1.run))
    thread_L.append(threading.Thread(name=host2.__str__(), target=host2.run))
    thread_L.append(threading.Thread(name=host3.__str__(), target=host3.run))
    thread_L.append(threading.Thread(name=host4.__str__(), target=host4.run))

    #Router threads
    thread_L.append(threading.Thread(name=router_a.__str__(), target=router_a.run))
    thread_L.append(threading.Thread(name=router_b.__str__(), target=router_b.run))
    thread_L.append(threading.Thread(name=router_c.__str__(), target=router_c.run))
    thread_L.append(threading.Thread(name=router_d.__str__(), target=router_d.run))

    #Link Layer thread
    thread_L.append(threading.Thread(name="Network", target=link_layer.run))
    
    for t in thread_L:
        t.start()
    
    
    #create some send events    
    for i in range(1):
        host1.udt_send(4, 'Somebody once told me the world is going to roll me. I aint the sharpest tool in the shed.')
        host2.udt_send(3, 'Heeeeeyyyy Yeaaaahh')
        #client.udt_send(2,'Sample data %d' %i)
    
    
    #give the network sufficient time to transfer all packets before quitting
    sleep(simulation_time)
    
    #join all threads
    for o in object_L:
        o.stop = True
    for t in thread_L:
        t.join()
        
    print("All simulation threads joined")



# writes to host periodically