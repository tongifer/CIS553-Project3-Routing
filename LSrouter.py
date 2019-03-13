####################################################
# LSrouter.py
# Names: Tong Pow, James Xue
# Penn IDs: 84233063, 51632014
#####################################################

import sys
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads


class LSrouter(Router):
    """Link state routing protocol implementation."""

    def __init__(self, addr, heartbeatTime):
        """TODO: add your own class fields and initialization code here"""
        Router.__init__(self, addr)  # initialize superclass - don't remove
        self.addr = addr
        self.heartbeatTime = heartbeatTime
        self.lastTime = 0
        self.neighbors = {}  # {endpoint: {port, sequence}
        self.graph = {}  # directly connected neighbors: cost of link
        self.packets = {}  # {addr: packet}
        self.tentative = {}
        self.confirmed = {
            addr: {
                'cost': 0,
                'nextHop': None
            }
        }
        self.mysqn = 0

    def handlePacket(self, port, packet):
        """TODO: process incoming packet"""

        # nextNeighbors = content['neighbors']
        # packet_graph = content['graph']

        if packet.isTraceroute():
            if packet.dstAddr in self.confirmed:
                self.send(self.neighbors[self.confirmed[packet.dstAddr]["nextHop"]]['port'], packet)

        # Distribute information on map
        elif packet.isRouting():
            content = loads(packet.content)
            print(self.addr, content)
            if packet.srcAddr not in self.packets or content['sqn'] > loads(self.packets[packet.srcAddr].content)['sqn']:
                self.packets[packet.srcAddr] = packet
                for n in self.neighbors:
                    #p = Packet(2, self.addr, n, content=dumps(content))
                    if port != self.neighbors[n]['port']:
                        self.send(self.neighbors[n]['port'], packet)

            # Create + update map
            self.graph = {}
            for packet_addr in self.packets:
                curr_content = loads(self.packets[packet_addr].content)
                curr_cost = curr_content['neighbors'][self.addr]['cost']

                if packet_addr not in self.graph:
                    self.graph[packet_addr] = {self.addr: curr_cost}
                    # print(packet_addr, self.addr, packet_addr, curr_cost)
                else:
                    self.graph[packet_addr][self.addr] = curr_cost
                if self.addr not in self.graph:
                    self.graph[self.addr] = {packet_addr: curr_cost}
                else:
                    self.graph[self.addr][packet_addr] = curr_cost

                #     if self.addr not in self.graph:
                #         self.graph[self.addr] = {packet_addr: self.packets[packet_addr].content['cost']}
                #     else:
                #         self.graph[self.addr][packet_addr] = self.packets[packet_addr].content['cost']
                # else:
                #     if self.addr not in self.graph

            # Populate self.tentative with this packet's neighbors
            # for neighbor in nextNeighbors:
            #     # Update self.graph
            #     if packet.srcAddr not in self.graph:
            #         self.graph[packet.srcAddr] = {neighbor: packet_graph[packet.srcAddr][neighbor]}
            #     else:
            #         self.graph[packet.srcAddr][neighbor] = min(self.graph[packet.srcAddr][neighbor], packet_graph[packet.srcAddr][neighbor])
            self.tentative = {}
            self.confirmed = {}

            # Place current node into self.tentative
            self.tentative[packet.srcAddr] = {
                'cost': 0,
                'nextHop': None
            }

            # Djikstra's, updating shortest path
            while self.tentative:
                # Pop lowest cost member
                lowestCostEntry = min(self.tentative, key=lambda k: self.tentative[k]['cost'])

                # Iterate through neighbors of lowestCostEntry, update
                curr_neighbors = self.graph[lowestCostEntry]
                for n in curr_neighbors:
                    # print(self.tentative, self.confirmed, curr_neighbors)

                    newCost = self.tentative[lowestCostEntry]['cost'] + curr_neighbors[n]
                    tentativeCost = float('inf')
                    if n in self.tentative:
                        tentativeCost = self.tentative[n]['cost']

                    # If found lower cost path, update tentative and graph
                    if (n not in self.confirmed and n not in self.tentative) or (n in self.tentative and newCost < tentativeCost):
                        self.tentative[n] = {
                            'cost': newCost,
                            'nextHop': lowestCostEntry
                        }

                # Update self.confirmed and pop
                self.confirmed[lowestCostEntry] = self.tentative[lowestCostEntry]
                del self.tentative[lowestCostEntry]

    def handleNewLink(self, port, endpoint, cost):
        """TODO: handle new link"""
        if endpoint not in self.neighbors:
            self.neighbors[endpoint] = {"port": port, "sqn": 0, "cost": cost}
            # self.graph[self.addr] = {endpoint: cost}

        for k, v in self.neighbors.iteritems():
            packet = Packet(Packet.ROUTING, self.addr, k)
            content = dumps(self.neighbors)
            self.send(v['port'], packet)

    def handleRemoveLink(self, port):
        """TODO: handle removed link"""
        pass

    def sendRoutingPacket(self):
        """Helper function that sends routing packets to all other nodes in network"""
        content = {
            #'graph': {A: {B: cost, ...}, ...}
            'sqn': self.mysqn,
            'neighbors': self.neighbors
        }
        for n in self.neighbors:
            p = Packet(2, self.addr, n, content=dumps(content))
            self.send(self.neighbors[n]['port'], p)

    def handleTime(self, timeMillisecs):
        """TODO: handle current time"""
        if timeMillisecs - self.lastTime > self.heartbeatTime:
            self.sendRoutingPacket()
            self.lastTime = timeMillisecs
            self.mysqn += 1

    def debugString(self):
        """TODO: generate a string for debugging in network visualizer"""
        return ""
