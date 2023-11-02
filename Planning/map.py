import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FILEPATH = "E:\\BFMC\\Planning\\bfmc.graphml"

# Take <graph> element from inside of <graphml> element and delete graphml 
# d2: dotted, d1: y, d0: x

# We need to convert python lists to np array so that we can keep track of the indexes when removing
# This version has duplicates in edges

class Edge():
    def __init__(self) -> None:
        self.source = None
        self.target = None
        self.is_dotted = False

    def __str__(self) -> str:
        return f"Edge that connects {self.source} to {self.target} | dotted: {self.is_dotted}"
    

class Node():
    def __init__(self) -> None:
        self.ID = None
        self.X = None
        self.Y = None

        self.preceding_nodes = []
        self.preceding_count = 0
        self.following_nodes = []
        self.following_count = 0

    def __str__(self) -> str:
        return f"Node {self.ID} at: {self.X, self.Y}, preceding nodes {self.preceding_nodes}, following nodes {self.following_nodes}"
    
    def update_counts(self):
        self.preceding_nodes = list(set(self.preceding_nodes))
        self.preceding_count = len(self.preceding_nodes)

        self.following_nodes = list(set(self.following_nodes))
        self.following_count = len(self.following_nodes)



class Graph():
    def __init__(self) -> None:
        self.edges = []
        self.nodes = {}

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    def add_node(self, node: Node):
        assert type(node.ID) == int
        self.nodes[node.ID] = node  

    def generate_connections(self):
        for edge in self.edges:
            preceding_node = edge.source
            following_node = edge.target

            self.nodes[preceding_node].following_nodes.append(following_node)
            self.nodes[following_node].preceding_nodes.append(preceding_node)

        for node in self.nodes.values():
            node.update_counts()

    
    def is_reachable(self, start: Node, finish: Node) -> bool:
        pass


    def get_nodes(self, get_IDs=False):
        # Get All Nodes
        IDs = list()
        Xs   = list()
        Ys   = list()

        for ID, node in self.nodes.items():
            IDs.append(ID)
            Xs.append(node.X)
            Ys.append(-node.Y) # Rotate orientation in order to match the graph on GitHub

        if get_IDs:
            return Xs, Ys, IDs
        
        return Xs, Ys
    
    def get_nodes_with_multiple_connections(self, preceding=2, following=2, get_IDs=False):
        IDs = list()
        Xs   = list()
        Ys   = list()

        for ID, node in self.nodes.items():
            if (node.preceding_count >= preceding or node.following_count >= following):
                IDs.append(ID)
                Xs.append(node.X)
                Ys.append(-node.Y) # Rotate orientation in order to match the graph on GitHub

        if get_IDs:
            return Xs, Ys, IDs
        
        return Xs, Ys
    
    def get_decision_nodes(self):
        return self.get_nodes_with_multiple_connections(get_IDs=True)
    



class DataReader():
    def __init__(self, file, map) -> None:
        tree = ET.parse(file)
        self.root = tree.getroot()
        self.map = map

        self.check_duplicate_nodes = False

    def parse_nodes(self):
        for child in self.root:
            if child.tag == "node":
                _node = Node()
                _node.ID = int(child.attrib["id"])
                for data in child:
                    if data.attrib["key"] == "d0":
                        _node.X = float(data.text)
                    elif data.attrib["key"] == "d1":
                        _node.Y = float(data.text)
                self.map.add_node(_node)

        if self.check_duplicate_nodes:
            self.fix_duplicate_nodes()

    
    def fix_duplicate_nodes(self):
        X, Y, IDs = Map.get_nodes(get_IDs=True)
        df = pd.DataFrame(X, Y)
        df.reset_index(inplace=True)
        df.index = IDs
        df.columns = ["X", "Y"]

        duplicates = df.sort_values(["X", "Y"], ascending=True)

        # print(duplicates)

        self.dup_map = {}

        register_ID = duplicates.index[0]
        register_X, register_Y = duplicates["X"].iloc[0], duplicates["Y"].iloc[0]
        for ID, X, Y in zip(duplicates.index[1:], duplicates["X"].iloc[1:], duplicates["Y"].iloc[1:]):
            if (register_X == X and register_Y == Y):
                self.map.nodes.pop(ID)
                print(f"Popped {ID} and replaced with {register_ID}")
                self.dup_map[ID] = register_ID
            else:
                register_ID = ID
                register_Y = Y
                register_X = X
                # print("Resetted register")



    def fix_duplicate_node(self):
        X, Y, IDs = Map.get_nodes(get_IDs=True)
        XY = pd.Series([(x, y) for x, y in zip(X, Y)])
        XY.index = IDs
        duplicates = XY[XY.duplicated()]

        self.dup_map = {}

        register_ID = duplicates.index[0]
        register_XY = duplicates.iloc[0]
        for ID, coordinate in zip(duplicates.index[1:], duplicates.iloc[1:]):
            # print(ID, coordinate)
            if (register_XY == coordinate):
                self.map.nodes.pop(ID)
                print(f"Popped {ID} and replaced with {register_ID}")
                self.dup_map[ID] = register_ID
            else:
                register_ID = ID
                register_XY = coordinate
                # print("Resetted register")


    def parse_edges(self):
        for child in self.root:
            if child.tag == "edge":
                _edge = Edge()

                _edge.source = int(child.attrib["source"])
                if self.check_duplicate_nodes:
                    if _edge.source in self.dup_map: _edge.source = self.dup_map[_edge.source]

                _edge.target = int(child.attrib["target"])
                if self.check_duplicate_nodes:
                    if _edge.target in self.dup_map: _edge.target = self.dup_map[_edge.target]

                for data in child:
                    if data.text == "True":
                        _edge.is_dotted = True
                self.map.add_edge(_edge)
        #if self.check_duplicate_nodes:
        #    self.fix_duplicate_edges()

    
    def fix_duplicate_edges(self):
        #DEPR
        sources = pd.Series([edge.source for edge in self.map.edges])
        targets = pd.Series([edge.target for edge in self.map.edges])
        df = pd.DataFrame(sources, targets)
        df.reset_index(inplace=True)
        df.columns = ["src", "trg"]
        duplicates = df.sort_values(["src", "trg"], ascending=True)

        reg_S, reg_T = duplicates["src"].iloc[0], duplicates["trg"].iloc[0]
        for ind, src, trg in zip(duplicates.index[1:], duplicates["src"].iloc[1:], duplicates["trg"].iloc[1:]):
            if reg_S == src and reg_T == trg:
                self.map.edges.pop(ind)
                print(f"Popped {ind}, edge: {src, trg}")
            else:
                reg_S = src
                reg_T = trg
                # print("Resetted register")


def main():
    global Map
    Map = Graph()
    data = DataReader(FILEPATH, Map)
    data.check_duplicate_nodes = True
    data.parse_nodes()
    data.parse_edges()
    Map.generate_connections()
    return Map


if __name__=="__main__":
    main()
    X, Y, IDs = Map.get_nodes_with_multiple_connections(get_IDs=True)
    XX, YY = Map.get_nodes()
    plt.scatter(x=XX, y=YY, color="blue")
    plt.scatter(x=X, y=Y, color="red")

    plt.show()



