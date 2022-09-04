import pygame
import heapq

vec = pygame.math.Vector2 #Vector class; vec(1,2) , v.x = 1, v.y =2
def vec2int(v): #Converts vectors into integers 
	return (int(v.x), int(v.y))

class Grid:
	def __init__(self, walls, width, height):
		self.width = width
		self.height = height
		self.weights = {}
		self.walls = walls
		self.connections = [vec(1, 0), vec(-1, 0), vec(0, 1), vec(0, -1), vec(1, 1), vec(-1, 1), vec(1, -1), vec(-1, -1)]

	def in_bounds(self, node): #Check if node is within window
		return 0 <= node.x < self.width and 0 <= node.y < self.height

	def passable(self, node): #Checks if passable 
		return node not in self.walls

	def find_neighbors(self, node):
		neighbors = [node + connection for connection in self.connections]
		neighbors = filter(self.in_bounds, neighbors)
		neighbors = filter(self.passable, neighbors)
		return neighbors

	def cost(self, from_node, to_node):
		if (vec(to_node) - vec(from_node)).length_squared() == 1: #Checks for orthogonal movement
			return self.weights.get(to_node, 0) + 10
		else:
			return self.weights.get(to_node, 0) + 14 #Diagonal movement is more weighted 

def heuristic(a, b):
    return (abs(a.x - b.x) + abs(a.y - b.y)) * 10

class PriorityQueue: #Sort the queue based on shortest distance
    def __init__(self):
        self.nodes = []

    def put(self, node, cost):
        heapq.heappush(self.nodes, (cost, node)) #Takes the nodes, sorts by the 'cost' (distance)

    def get(self):
        return heapq.heappop(self.nodes)[1] #Takes out lowest value

    def empty(self): #Checks if nodes are left
        return len(self.nodes) == 0

def a_star_search(graph, start, end): #Input the map grid, start position, and end position
    frontier = PriorityQueue() #Creates a "PriotyQueue" object for node list
    frontier.put(vec2int(start), 0) #Starting position 
    path = {} #Dictionary of direction vectors
    cost = {} #Dictionary of movement cost
    path[vec2int(start)] = None #Start vector
    cost[vec2int(start)] = 0 #Start cost

    while not frontier.empty():  #If there are still nodes 
        current = frontier.get() #Update node to the lowest cost from the PriorityQueue
        if current == end: #If path is found, stop loop 
            break
        
        for next in graph.find_neighbors(vec(current)): #Searches within graph for next available tile (find_neighbor) 
            next = vec2int(next) #Converts node to integer
            next_cost = cost[current] + graph.cost(current, next) #Calculates cost of movement
            if next not in cost or next_cost < cost[next]: #If node not already tested or worth less than existing node
                cost[next] = next_cost #Add to dictionary 
                priority = next_cost + heuristic(end, vec(next)) #Totals the cost and distance values
                frontier.put(next, priority) #Add the node 
                path[next] = vec(current) - vec(next) #Adds the node to the path
    return path, cost

