import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import map as Map

map = Map.main()

class VectorWalk():
    def __init__(self,
                 start_node,
                 end_node,
                 map=map,
                 step_limit=9999) -> None:
        
        self.start_node : Map.Node = map.nodes[start_node]
        self.end_node   : Map.Node = map.nodes[end_node]

        self.current_node = self.start_node
        
        self.path = list()
        self.visited_nodes = list()
        self.map = map

        self.global_direction_vector = np.array([self.end_node.X - self.start_node.X,
                                                 self.end_node.Y - self.start_node.Y])
        
    def get_vector(self, start, end):
        return np.array([end.X - start.X,
                         end.Y - start.Y])
        
    def step(self):
        if self.current_node.following_count < 1:
            ValueError("There are not any possible action")
        
        elif self.current_node.following_count == 1:
            self.keep_track_of_the_path()
            next_node_id = self.current_node.following_nodes[0]
            self.update_current_node(self.map.nodes[next_node_id])
            print(f"Keeping the lane, next node: {self.current_node.ID}..")

        else:
            reachable_nodes = self.current_node.following_nodes
            target_vector = self.get_vector(start=self.current_node, end=self.end_node)
            
            rewards = pd.Series([])
            for node_id in reachable_nodes:
                #print(f"DEBUG: NODEID {node_id}, VISITED {self.visited_nodes}")
                print(f"#DEBUG {self.current_node.ID, node_id}")
                if node_id not in self.visited_nodes:
                    node = self.map.nodes[node_id]
                    next_node_vector = self.get_vector(self.current_node, node)
                    last_node_vector = self.get_vector(self.current_node, self.path[-1])
                    backwards = np.dot(next_node_vector, last_node_vector)
                    if True:
                        first_reward = np.dot(target_vector, next_node_vector)
                        future_reward = self.future_step(node)
                        rewards[node_id] = first_reward + future_reward

            max_gain_ind = rewards.idxmax()
            self.keep_track_of_the_path()
            print(f"Evaluated nodes (at {self.current_node.ID}):\n{rewards}")
            self.update_current_node(self.map.nodes[max_gain_ind])
            print(f"Decided on {self.current_node}, continuing..")

    
    def future_step(self, node, n = 5):
            total_reward = 0
            counter = 0
            simulation_node = node

            while (simulation_node != self.end_node):
                #print(f"#DEBUG: iter {counter}, sim_node {simulation_node.ID}")
                if counter == n: break
                counter += 1

                if simulation_node.following_count < 1:
                    ValueError("There are not any possible action")
                    total_reward -= 99999
                    break

                elif self.current_node.following_count == 1:
                    target_vector = self.get_vector(start=simulation_node, end=self.end_node)

                    next_node= self.map.nodes[self.current_node.following_nodes[0]]
                    node_vector = self.get_vector(simulation_node, next_node)

                    reward = np.dot(target_vector, node_vector)
                    total_reward += reward

                    simulation_node = next_node
                    
                else:
                    reachable_nodes = simulation_node.following_nodes
                    target_vector = self.get_vector(start=simulation_node, end=self.end_node)
                    
                    products = pd.Series([])
                    for node_id in reachable_nodes:
                        if node_id not in self.visited_nodes:
                            node = self.map.nodes[node_id]
                            node_vector = self.get_vector(simulation_node, node)
                            products[node_id] = np.dot(target_vector, node_vector)

                    try:
                        max_gain_ind = products.idxmax()
                    except ValueError:
                        total_reward -= 99999
                        break
                    total_reward += products.max()
                    simulation_node = self.map.nodes[max_gain_ind]

            return total_reward
                
            

    def walk(self):
        while self.current_node != self.end_node:
            self.visited_nodes.append(self.current_node.ID)
            self.step()
            #input()
        print(f"Reached the node! Total steps taken: {len(self.path)}")
        return self.path


    def keep_track_of_the_path(self):
        self.path.append(self.current_node)


    def update_current_node(self, node: Map.Node):
        self.current_node = node


class WalkOptimizer():
    def __init__(self,
                 start_node,
                 end_node,
                 map=map,
                 step_limit=9999) -> None:
        
        self.start_node : Map.Node = map.nodes[start_node]
        self.end_node   : Map.Node = map.nodes[end_node]
        self.map = map


    def optimize(self):
        #end_node walk
        end_note = self.end_node
        walk = VectorWalk(self.start_node.ID,
                          self.end_node.ID,
                          self.map)
        path = walk.walk()

        n = 5
        if self.find_preceding_cone(n) == -1:
            return path

        upto_walk =VectorWalk(self.start_node.ID,
                          self.end_node.ID,
                          self.map)
        upto_path = upto_walk.walk()

        to_walk = VectorWalk(self.end_node.ID,
                            end_note.ID,
                            self.map)
        to_path = to_walk.walk()

        if (len(upto_path) + len(to_path) < len(path)):
            print(f"Use node {self.end_node.ID} for faster reach")


    def find_preceding_cone(self, n):
        junction_on_the_back = False
        for i in range(0, n):
            if self.end_node.preceding_count > 1:
                junction_on_the_back = True

            else:
                self.end_node = self.map.nodes[\
                    self.end_node.preceding_nodes[0]]
                
                print(f"New node: {self.end_node}")
        if junction_on_the_back:
            return -1
        
        else:
            return 0


                    
            
walk = VectorWalk(start_node=196, end_node=366, map=map)
path = walk.walk()

pathX = []
pathY = []
for node in path: 
    pathX.append(node.X)
    pathY.append(-node.Y)

X, Y, IDs = map.get_nodes_with_multiple_connections(get_IDs=True)
XX, YY = map.get_nodes()
plt.scatter(x=XX, y=YY, color="black", s=0.3)
plt.plot(pathX, pathY, color="orange")
plt.scatter(x=X, y=Y, color="purple")
plt.scatter(x=pathX[0], y=pathY[0], color="green")
plt.scatter(x=pathX[-1], y=pathY[-1], color="red")

plt.show()