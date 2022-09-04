import pygame
import math 
import random
import enemy_pathfinder as pf 

## ((408, 312)) # 17 x 13 tiles 
# 408 * 3 =  1224
# 312 * 2 = 624

def Load_Sprites(spritesheet, rectangle, colorkey = None):
    rect = pygame.Rect(rectangle) #Create rectangle 
    frame = pygame.Surface(rect.size) #Create surface from rectangle size
    frame.blit(spritesheet, (0,0), rect) #Draws frame onto surface
    if colorkey is not None:
        frame.set_colorkey(colorkey, pygame.RLEACCEL) #Set transparency
    return frame


class Characters(object):
	def __init__(self, x, y, width, height, color):
		self.x = x
		self.y = y
		self.width = width
		self.height = height		
		self.color = color
		self.tile =[0, 0] 

		self.bullets=[]
		self.cooldown = 0
		self.invul = 0 
		self.health = 1

		#Load Sprites
		self.frame = 0
		self.spritesheet = pygame.image.load("Bulbasaur.png").convert() 
		self.sprites = []
		for y in range(2):
			for x in range(15):
				self.sprites.append(Load_Sprites(self.spritesheet, (x*30,y*30,30,30), colorkey=(0,128,192)))
		#Animation States
		self.direction = 'Left'
		self.flip = 0
		self.walk = False
		self.attack = False 
		self.hit = False
		self.knocked = False
		self.frame_dictionary = {'Down': {'Hit': 25, 'Attack': 15, 'Walk':0}, 
								'Down Left': {'Hit': 26, 'Attack': 17, 'Walk':3},  
								'Left': {'Hit': 27, 'Attack': 19, 'Walk':6},
								'Up Left': {'Hit': 28, 'Attack': 21, 'Walk':9},
								'Up': {'Hit': 29, 'Attack': 23, 'Walk':12},
								'Down Right': {'Hit': 26, 'Attack': 17, 'Walk':3},  
								'Right': {'Hit': 27, 'Attack': 19, 'Walk':6},
								'Up Right': {'Hit': 28, 'Attack': 21, 'Walk':9},
								}

		#Screen Scroll
		self.scroll_x = 0
		self.scroll_y = 0 

	def frames(self):
		if self.walk or self.attack:
			self.frame += 0.25 

		if self.hit:
			self.frame = self.frame_dictionary[self.direction]['Hit'] #Hit frame
		elif self.attack:
			if self.frame<self.frame_dictionary[self.direction]['Attack'] or self.frame>self.frame_dictionary[self.direction]['Attack']+1.75:
				self.frame = self.frame_dictionary[self.direction]['Attack'] #Set to attack frame
		elif self.walk:
			if self.frame<self.frame_dictionary[self.direction]['Walk'] or self.frame>self.frame_dictionary[self.direction]['Walk']+2.75:
				self.frame = self.frame_dictionary[self.direction]['Walk']
		else: #Standing still 
			self.frame = self.frame_dictionary[self.direction]['Walk']
				
		if self.frame>self.frame_dictionary[self.direction]['Attack']+1:
			self.attack = False #Toggles "Attack" state
		
		if not self.invul:
			self.hit = False #Once invulnerability ends, toggle "Hit" state

		if self.direction == 'Down Right' or self.direction == 'Right' or self.direction == 'Up Right':
			self.flip = 1
		else:
			self.flip = 0

class Enemies(object):
	def __init__(self,x,y, width, height, color, screen ):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.color = color
		self.screen = screen
		self.invul = False
		self.health = 1
		self.speed = 1.25
		self.tile = []
		self.wait = 0
		self.path = []
		self.tracker = 0 
		#Load Frames
		self.frame = 0
		self.spritesheet = pygame.image.load("Grimer.png").convert() 
		self.sprites = []
		for y in range(2):
			for x in range(15):
				self.sprites.append(Load_Sprites(self.spritesheet, (x*30,y*30,30,30), colorkey=(0,128,192)))

		#Animation States
		self.direction = 'Left'
		self.flip = 0
		self.hit = False 
		self.attack = False 
		self.walk = True
		self.knocked = False
		self.frame_dictionary = {'Down': {'Hit': 25, 'Attack': 15, 'Walk':0}, 
								'Down Left': {'Hit': 26, 'Attack': 17, 'Walk':3},  
								'Left': {'Hit': 27, 'Attack': 19, 'Walk':6},
								'Up Left': {'Hit': 28, 'Attack': 21, 'Walk':9},
								'Up': {'Hit': 29, 'Attack': 23, 'Walk':12},
								'Down Right': {'Hit': 26, 'Attack': 17, 'Walk':3},  
								'Right': {'Hit': 27, 'Attack': 19, 'Walk':6},
								'Up Right': {'Hit': 28, 'Attack': 21, 'Walk':9},
								}
		self.direct_dict = {(1,0):'Right', (1,-1): 'Up Right', (1,1): 'Down Right',
							(-1,0):'Left', (-1,-1): 'Up Left', (-1,1):'Down Left',
							(0,1):'Down',(0,-1):'Up' }
		#[unit.left,unit.right,unit.front,unit.back] 

	def frames(self):
		if self.hit:
			self.frame = self.frame_dictionary[self.direction]['Hit'] #Hit frame
		elif self.attack:
			if self.frame<self.frame_dictionary[self.direction]['Attack'] or self.frame>self.frame_dictionary[self.direction]['Attack']+1:
				self.frame = self.frame_dictionary[self.direction]['Attack'] #Set to attack frame
		elif self.walk:
			if self.frame<self.frame_dictionary[self.direction]['Walk'] or self.frame>self.frame_dictionary[self.direction]['Walk']+2:
				self.frame = self.frame_dictionary[self.direction]['Walk']
		else: #Standing still 
			self.frame = self.frame_dictionary[self.direction]['Walk']
		
		if self.walk or self.attack:
			self.frame += 0.25 
		
		if self.frame>self.frame_dictionary[self.direction]['Attack']+1:
			self.attack = False #Toggles "Attack" state
		
		if not self.invul:
			self.hit = False #Once invulnerability ends, toggle "Hit" state

		if self.direction == 'Down Right' or self.direction == 'Right' or self.direction == 'Up Right':
			self.flip = 1
		else:
			self.flip = 0

def Move_Object(obj, height, width, BG, Tile):
	speed = 5
	#Replace with nested dictionary too 
	direction_dict = {'Up Left': [-0.707,-0.707], 'Up Right': [0.707, -0.707], 'Right':[1,0],
					'Up': [0,-1], 'Down Left': [-0.707, 0.707],'Left':[-1, 0] ,
					'Down Right':[0.707, 0.707], 'Down': [0,1], }

	if pygame.key.get_pressed()[pygame.K_w]:
		if pygame.key.get_pressed()[pygame.K_a]: #Move Up-Left
			obj.direction = 'Up Left'
			obj.walk = True
		elif pygame.key.get_pressed()[pygame.K_d]: #Move Up-Right
			obj.direction = 'Up Right'
			obj.walk = True
		else: #Move Up 
			obj.direction = 'Up' 
			obj.walk = True
	elif pygame.key.get_pressed()[pygame.K_s]:
		if pygame.key.get_pressed()[pygame.K_a]: #Move Down-Left
			obj.direction = 'Down Left' 
			obj.walk = True
		elif pygame.key.get_pressed()[pygame.K_d]: #Move Down-Right
			obj.direction = 'Down Right' 
			obj.walk = True
		else: #Move Down
			obj.direction = 'Down' 
			obj.walk = True
	elif pygame.key.get_pressed()[pygame.K_a]: #Move Left
		obj.direction = 'Left' 
		obj.walk = True
	elif pygame.key.get_pressed()[pygame.K_d]: #Move Right
		obj.direction = 'Right'
		obj.walk = True
	else:
		obj.walk = False
	#Projects where tile will go 
	#X tile (different for offset)
	if direction_dict[obj.direction][0]>0:
		obj.tile[0] = round((-0.5*obj.width + obj.x + speed*direction_dict[obj.direction][0])/Tile.tile)
	else:
		obj.tile[0] = round((-obj.width+obj.x + speed*direction_dict[obj.direction][0])/Tile.tile) #Left side
	#Y tile 
	obj.tile[1] = round((obj.y + speed*direction_dict[obj.direction][1])/Tile.tile)

	#Checks if future tile is a boundary 
	#If in the wall list, set speed vector to 0 
	for wall in Tile.walls:
		if obj.tile == wall:
			if obj.tile[0] == wall[0]:
				direction_dict[obj.direction][0] = 0

			if obj.tile[1] == wall[1]:
				direction_dict[obj.direction][1] = 0 

	#Move object 
	if obj.walk:
		obj.x += speed*direction_dict[obj.direction][0]
		obj.y += speed*direction_dict[obj.direction][1]

	#Screen boundaries (final check)
	if obj.x < 0: #If object exceeds left boundary
		obj.x = 0
	elif obj.x > width-obj.width/2: #If object exceeds right boundary
		obj.x = width-obj.width/2

	if obj.y < 0: #If object exceeds top boundary
		obj.y = 0
	elif obj.y > height-obj.height/2: #If object exceeds bottom boundary
		obj.y = height-obj.height/2	
def Screen_Scroll(obj, enemies, BG):
	if obj.scroll_x != 0 or obj.scroll_y != 0:
		for enemy in enemies:
			enemy.x += obj.scroll_x
			enemy.y += obj.scroll_y
		BG.x += obj.scroll_x
		BG.y += obj.scroll_y

class Projectiles(object):
	def __init__(self, x, y, direction, color, speed):
		self.x = x
		self.y = y
		self.color = color
		self.direction = direction
		self.speed = speed
		self.radius = 3
	def Move(self, win):
		if self.direction == 'Up Left':
			self.x -= self.speed * 0.707
			self.y -= self.speed * 0.707
		elif self.direction == 'Up':
			self.y -= self.speed
		elif self.direction == 'Up Right':
			self.x += self.speed * 0.707
			self.y -= self.speed * 0.707
		elif self.direction == 'Right':
			self.x += self.speed
		elif self.direction == 'Down Right':
			self.x += self.speed * 0.707
			self.y += self.speed * 0.707
		elif self.direction == 'Down':
			self.y += self.speed
		elif self.direction == 'Down Left':
			self.x -= self.speed * 0.707
			self.y += self.speed * 0.707
		elif self.direction == 'Left':
			self.x -= self.speed

		pygame.draw.circle(win, self.color, (round(self.x), round(self.y)), self.radius)

def Shoot(obj):
	if pygame.key.get_pressed()[pygame.K_j]:
		if obj.cooldown == 0:
			obj.attack = True 
			obj.bullets.append(Projectiles(obj.x, obj.y, obj.direction, (255,255,255), 5))
			obj.cooldown = 10
	if obj.cooldown>0:
		obj.cooldown -= 1
def Proj_Collision(obj, proj, enemy):
	if proj.x < 0: #If object exceeds left boundary
		obj.bullets.pop(obj.bullets.index(proj)) 
	elif proj.x > 400-proj.radius: #If object exceeds right boundary
		obj.bullets.pop(obj.bullets.index(proj)) 
	if proj.y < 0: #If object exceeds top boundary
		obj.bullets.pop(obj.bullets.index(proj)) 
	elif proj.y > 300-proj.radius: #If object exceeds bottom boundary
		obj.bullets.pop(obj.bullets.index(proj)) 

	if enemy.health>0:
		if proj.x > enemy.x and proj.x < enemy.x+enemy.width:
			if proj.y > enemy.y and proj.y < enemy.y+enemy.height: 
				obj.bullets.pop(obj.bullets.index(proj)) 
				enemy.hit = True
				enemy.health -= 1
def Object_Collision(hunter, target):
	knock_back = 10
	if not target.invul:
		if hunter.x+hunter.width>target.x and hunter.x<target.x: #Right boundary
			if hunter.y<target.y+target.height and hunter.y+hunter.height>target.y+target.height: 
				target.knocked = True
				target.hit = True #Hit from bottom left
			elif hunter.y+hunter.height>target.y and hunter.y<target.y:
				target.knocked = True
				target.hit = True #Hit from top left
			elif hunter.y == target.y or hunter.y+hunter.height == target.y+target.height:
				target.knocked = True
				target.hit = True #Hit from left 
		elif hunter.x+hunter.width>target.x+target.width and hunter.x<target.x+target.width: #Left boundary
			if hunter.y<target.y+target.height and hunter.y+hunter.height>target.y+target.height: 
				target.knocked = True
				target.hit = True #Hit from bottom right
			elif hunter.y+hunter.height>target.y and hunter.y<target.y:
				target.knocked = True
				target.hit = True #Hit from top right
			elif hunter.y == target.y or hunter.y+hunter.height == target.y+target.height:
				target.knocked = True
				target.hit = True #Hit from right
		elif hunter.y+hunter.height>target.y+target.height and hunter.y<target.y+target.height:
			if hunter.x == target.x or hunter.x+hunter.width == target.x+target.width:
				target.knocked = True
				target.hit = True #Hit from bottom
		elif hunter.y+hunter.height>target.y and hunter.y<target.y: #Bottom boundary
			if hunter.x == target.x or hunter.x+hunter.width == target.x+target.width:
				target.knocked = True
				target.hit = True #Hit from top 
		else:
			target.knocked = False
			target.hit = False

	if target.knocked:
		target.invul = 10
		target.health -= 1

		if hunter.x - target.x > 5: #Knock left
			if hunter.y - target.y > 5: #Knock up left
				target.x -= knock_back *.707
				target.y -= knock_back *.707
			elif target.y - hunter.y > 5: #Knock down left
				target.x -= knock_back *.707
				target.y += knock_back *.707				
			else:
				target.x -= knock_back
		elif target.x - hunter.x > 5: #Knock right
			if hunter.y - target.y > 5: #Knock up right
				target.x += knock_back *.707
				target.y -= knock_back *.707
			elif target.y - hunter.y > 5: #Knock down right
				target.x += knock_back *.707
				target.y += knock_back *.707				
			else:
				target.x += knock_back
		elif hunter.y - target.y > 5: #Knock up
			target.y -= knock_back
		elif target.y - hunter.y > 5:  #Knock down
			target.y += knock_back
		else:
			target.y += knock_back	
		target.knocked = False	
def Invulnerable(obj):
	if obj.invul > 0:
		obj.invul -= 1
def Hunt(hunter, target, width, height):
	if hunter.x>0 and hunter.x<width and hunter.y>0 and hunter.y<height: #Checks if object is on screen 
		if not target.invul: 
			if hunter.y>target.y:
				if hunter.x>target.x: #Move Up-Left
					hunter.x -= hunter.speed * 0.707
					hunter.y -= hunter.speed * 0.707
				elif hunter.x<target.x: #Move Up-Right
					hunter.x += hunter.speed * 0.707
					hunter.y -= hunter.speed * 0.707
				else: #Move Up 
					hunter.y -= hunter.speed
			elif hunter.y<target.y:
				if hunter.x>target.x: #Move Down-Left
					hunter.x -= hunter.speed * 0.707 
					hunter.y += hunter.speed * 0.707
				elif hunter.x<target.x: #Move Down-Right
					hunter.x += hunter.speed * 0.707
					hunter.y += hunter.speed * 0.707
				else: #Move Down
					hunter.y += hunter.speed
			elif hunter.x>target.x: #Move Left
				hunter.x -= hunter.speed
			elif hunter.x<target.x: #Move Right
				hunter.x += hunter.speed

			if hunter.x - target.x > 5: #Knock left
				if hunter.y - target.y > 5: #Knock up left
					hunter.direction = 'Up Left'
				elif target.y - hunter.y > 5: #Knock down left
					hunter.direction = 'Down Left'
				else:
					hunter.direction = 'Left'
			elif target.x - hunter.x > 5: #Knock right
				if hunter.y - target.y > 5: #Knock up right
					hunter.direction = 'Up Right'
				elif target.y - hunter.y > 5: #Knock down right
					hunter.direction = 'Down Right'
				else:
					hunter.direction = 'Right'
			elif hunter.y - target.y > 5: #Knock up
				hunter.direction = 'Up'
			elif target.y - hunter.y > 5:  #Knock down
				hunter.direction = 'Down'

class Background(object):
	def __init__(self,level, width, height, x, y):
		self.level = level
		self.width = width
		self.height = height
		self.x = x
		self.y = y
		self.background = pygame.image.load("TileBackground2.png").convert() 
		self.screen_x = 0
		self.screen_y = 0
		self.direction = [0,0]
		self.boundary_x = {0: [0,408], 1:[408,816], 2:[816,1224]}
		self.boundary_y = {0: [0,312], 1:[312,624]}
		self.scroll = False

		##Tile Loading
		self.tile_load = pygame.image.load("TileImport.png").convert()
		self.wall_tiles = []
		self.floor_tiles = []
		self.water_tiles = []
		for y in range(17):
			for x in range(3):
				##Wall Tiles
				self.wall_tiles.append(Load_Sprites(self.tile_load, (1+x*25,1+y*25,24,24)))
				self.floor_tiles.append(Load_Sprites(self.tile_load, (1+(x+9)*25,1+y*25,24,24)))
				self.water_tiles.append(Load_Sprites(self.tile_load, (1+(x+21)*25,1+y*25,24,24)))
		# for y in range(2):
		# 	for x in range(2):
		# 		self.wall_tiles.append(Load_Sprites(self.tile_load, (1+x*25,1+(y+15)*25,24,24)))
	## ((408, 312))

	def draw_bg(self, win):
		win.blit(self.background, (self.x, self.y))


	def screen_change(self, win, obj, enemies):
		#Triggers screen change when passing boundary 
		if not self.scroll:
			if obj.x > self.width - obj.width: #Player right
				self.scroll = True
				self.direction = [1, 0]
				self.screen_x += 1
			elif obj.x < obj.width: #Player left
				if self.screen_x>0:
					self.scroll = True	
					self.screen_x -= 1
					self.direction = [-1, 0]
			elif obj.y > self.height - obj.height: #Player down
				self.scroll = True	
				self.direction = [0, 1]
				self.screen_y += 1
			elif obj.y < obj.height/4: #Player up 
				if self.screen_y>0:
					self.scroll = True	
					self.screen_y -= 1
					self.direction = [0, -1]	
		else:
			self.x -= 24*self.direction[0] 
			self.y -= 24*self.direction[1]
			obj.x -= 24*self.direction[0]
			obj.y -= 24*self.direction[1]
			for enemy in enemies:
				enemy.x -= 24*self.direction[0]
				enemy.y -= 24*self.direction[1]

		if self.direction[0]>0:#Pushes player away from boundary after transition 
			if abs(self.x) >= self.boundary_x[self.screen_x][0]:
				if self.scroll:
					self.scroll = False
					if obj.x < obj.width:
						obj.x = obj.width  
		elif self.direction[0]<0:
			if abs(self.x) <= self.boundary_x[self.screen_x][0]:
				if self.scroll:
					self.scroll = False
					if obj.x> self.width - obj.width:
						obj.x = self.width - 1.5*obj.width
		elif self.direction[1]>0:
			if abs(self.y) >= self.boundary_y[self.screen_y][0]:
				if self.scroll:
					self.scroll = False
					if obj.y < obj.height/4:
						obj.y = obj.height/4	
		elif self.direction[1]<0:
			if abs(self.y) <= self.boundary_y[self.screen_y][0]:
				if self.scroll:
					self.scroll = False
					if obj.y > self.height - obj.height:
						obj.y = self.height - obj.height	

class Tiles:
	def __init__(self, tile, BG):
		self.tile = tile #Tile size 
		self.level_walls = {(0,0): [[0,0],[0,1],[0,2],[0,3],[0,4],[0,8],[0,9],[0,10],[0,11],[0,12], #Left wall [with exit]
					[16,0],[16,1],[16,2],[16,3],[16,4],[16,8],[16,9],[16,10],[16,11],[16,12], #Right wall [with exit]
					[1,0],[2,0],[3,0],[4,0],[5,0],[6,0],[7,0],[8,0],[9,0],[10,0],[11,0],[12,0],[13,0],[14,0],[15,0],[16,0], #Top wall 
					[1,12],[2,12],[3,12],[4,12],[5,12],[6,12],[10,12],[11,12],[12,12],[13,12],[14,12],[15,12],[16,12]],  #Bottom wall 

					(1,0): [[0,0],[0,1],[0,2],[0,3],[0,4],[0,8],[0,9],[0,10],[0,11],[0,12], [1,3], [1,4], #Left wall [with exit]
					[16,0],[16,1],[16,2],[16,3],[16,4],[16,5],[16,6],[16,7],[16,8],[16,9],[16,10],[16,11],[16,12], #Right wall [with exit]
					[1,0],[2,0],[3,0],[4,0],[5,0],[6,0],[7,0],[8,0],[9,0],[10,0],[11,0],[12,0],[13,0],[14,0],[15,0],[16,0], #Top wall 
					[1,12],[2,12],[3,12],[4,12],[5,12],[6,12],[10,12],[11,12],[12,12],[13,12],[14,12],[15,12],[16,12]],

					(0,1): [[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[0,7],[0,8],[0,9],[0,10],[0,11],[0,12], #Left wall [with exit]
					[16,0],[16,1],[16,2],[16,3],[16,4],[16,8],[16,9],[16,10],[16,11],[16,12], #Right wall [with exit]
					[1,0],[2,0],[3,0],[4,0],[5,0],[6,0],[10,0],[11,0],[12,0],[13,0],[14,0],[15,0],[16,0], #Top wall 
					[1,12],[2,12],[3,12],[4,12],[5,12],[6,12],[7,12],[8,12],[9,12],[10,12],[11,12],[12,12],[13,12],[14,12],[15,12],[16,12]],

					(1,1): [[0,0],[0,1],[0,2],[0,3],[0,4],[0,8],[0,9],[0,10],[0,11],[0,12], #Left wall [with exit]
					[16,0],[16,1],[16,2],[16,3],[16,4],[16,5],[16,6],[16,7],[16,8],[16,9],[16,10],[16,11],[16,12], #Right wall [with exit]
					[1,0],[2,0],[3,0],[4,0],[5,0],[6,0],[10,0],[11,0],[12,0],[13,0],[14,0],[15,0],[16,0], #Top wall 
					[1,12],[2,12],[3,12],[4,12],[5,12],[6,12],[10,12],[11,12],[12,12],[13,12],[14,12],[15,12],[16,12]],
					}
		self.x = 2
		self.y = 8
		self.tile_screen = (0,0)
		#self.rock = [[5,3], [5,4],[5,5], [6,3], [6,4], [6,5], [7,3], [7,4], [7,5], [self.x, self.y], [self.x+1, self.y], [self.x+1, self.y+1], [self.x+2, self.y]]
		self.rock = [[3, 3]]
		self.boulder = [ [7,3], [7, 4], [8,3], [8,4] ]
		self.row = [ [11,3], [12,3],[13,3] ]
		self.corner = [ [3,8], [3,9], [4,8]]
		self.tetris = [ [7,8], [8,8], [9,8], [8,9]]
		self.cross =  [ [11,8], [12,8], [13,8], [12,7], [12,9] ]

		self.level_walls[(0,0)] += self.rock + self.boulder + self.row + self.corner + self.tetris + self.cross
		self.walls = []
		self.map_list = [] #Adds tile to list (17 x 13 = 221 tiles)
		
		self.map_tiles = {} ## Create dictionary of keys
		for keys in self.level_walls.keys():
			self.map_tiles[keys] = []
		self.count = 0
		self.tile_type = 0

		##Create tiles
		for screen in self.level_walls:
			for y in range(0, round(BG.height / self.tile)):
				for x in range (0, round(BG.width / self.tile)): #Tile Size (17 x 13 = 221 tiles)
					if [x,y] in self.level_walls[screen]: #Find walls in screen
						if [x, y+1] in self.level_walls[screen]: #Top walls
							if [x+1, y] in self.level_walls[screen]: #Top Left corner
								if [x, y-1] in self.level_walls[screen]:
									if [x+1, y-1] not in self.level_walls[screen]:
										if [x+1, y] in self.level_walls[screen]:
											if [x-1, y] in self.level_walls[screen]:
												self.tile_type = 22
											else:
												self.tile_type = 30
										else:
											self.tile_type = 30 #Was 48?

									elif [x+1, y+1] not in self.level_walls[screen]:
										self.tile_type = 45						
									elif [x+1, y] in self.level_walls[screen]:
										if [x-1, y] in self.level_walls[screen]:
											self.tile_type = 4
										else:
											self.tile_type = 3
									else:
										self.tile_type = 3
								elif [x-1, y] in self.level_walls[screen]:
									if y-1 <= 0:
										if [x+1, y+1] not in self.level_walls[screen]:
											self.tile_type = 45
										elif [x-1, y+1] in self.level_walls[screen]:
											self.tile_type = 4
										else:
											self.tile_type = 46
									elif [x, y+1] in self.level_walls[screen]:
										self.tile_type = 28
									elif [x, y-1] in self.level_walls[screen]:
										self.tile_type = 34
									else:
										self.tile_type = 1
								elif y-1 <= 0:
									if [x+1, y+1] not in self.level_walls[screen]:
										self.tile_type = 45
									else:
										self.tile_type = 4
								elif [x+1, y+1] not in self.level_walls[screen]:
									self.tile_type = 9
								else:
									self.tile_type = 0
							elif [x-1, y] in self.level_walls[screen]: #Top Right corner
								if [x, y-1] in self.level_walls[screen]:
									if [x-1, y-1] not in self.level_walls[screen]:
										if [x, y+1] in self.level_walls[screen]:
											self.tile_type = 32
										else:
											self.tile_type = 49
									elif [x-1, y+1] not in self.level_walls[screen]:
										self.tile_type = 46						
									elif x+1<16:
										self.tile_type = 5
									else:
										self.tile_type = 4
								elif x+1<16:
									if [x-1, y+1] not in self.level_walls[screen]:
										self.tile_type = 11
									else:
										self.tile_type = 2
								# elif [x-1, y+1] not in self.level_walls[screen]:
								# 	self.tile_type = 46
								else:
									self.tile_type = 46
							elif x-1 <= 0: #Left wall
								if [x, y-1] in self.level_walls[screen]:
									self.tile_type = 5
								else:
									self.tile_type = 2 #Exit Bottom left corner 
							elif x+1 > 16: #Right wall
								if [x, y-1] in self.level_walls[screen]:
									self.tile_type = 3
								else:
									self.tile_type = 0
							elif [x-1, y] not in self.level_walls[screen] and [x+1, y] not in self.level_walls[screen]:
								if [x, y-1] in self.level_walls[screen]:
									self.tile_type = 12
								else:
									self.tile_type = 19
						elif [x, y-1] in self.level_walls[screen]: 
							if [x+1, y] in self.level_walls[screen]:
								if [x-1, y] in self.level_walls[screen]:
									if [x+1, y-1] not in self.level_walls[screen]:
										self.tile_type = 48
									elif [x-1, y-1] not in self.level_walls[screen]:
										self.tile_type = 49
									elif y+1<12:
										self.tile_type = 7
									else:
										self.tile_type = 4
								elif x-1 >0:
									if y+1> 12:
										self.tile_type = 3
									elif [x+1, y-1] not in self.level_walls[screen]:
										self.tile_type = 15								
									else:
										self.tile_type = 6
								elif y+1 > 12:
									self.tile_type = 48
								else:
									self.tile_type = 6

							elif [x-1, y] in self.level_walls[screen]: #Bottom Left corner
								if y+1 > 12:
									if [x-1, y-1] not in self.level_walls[screen]:
										self.tile_type = 49
									else:
										self.tile_type = 4						
								elif [x-1, y-1] not in self.level_walls[screen]:
									if [x, y+1] in self.level_walls[screen]:
										self.tile_type = 30
									else:
										self.tile_type = 17
								else:
									self.tile_type = 8							
							elif x-1 <= 0: #Left wall
								self.tile_type = 8
							elif x+1 > 16: #Right wall
								self.tile_type = 6
							elif [x-1, y] not in self.level_walls[screen] and [x+1, y] not in self.level_walls[screen]:
								self.tile_type = 25
						elif [x+1, y] in self.level_walls[screen]: #Side walls
							if y-1 <= 0:
								self.tile_type = 7 #Top wall
							elif y+1>12:
								if [x-1, y] not in self.level_walls[screen]:
									self.tile_type = 0
								else:
									self.tile_type = 1 #Bottom wall
							elif [x, y-1] not in self.level_walls[screen] and [x, y+1] not in self.level_walls[screen]:
								if [x-1, y] not in self.level_walls[screen]:
									self.tile_type = 21
								else: 
									self.tile_type = 10  #Bottom Left corner exit
						elif [x-1, y] in self.level_walls[screen]:
							if y-1 <= 0:
								self.tile_type = 8 #Bottom Right corner exit
							elif y+1>12:
								self.tile_type = 2 #Bottom wall
							elif [x, y-1] not in self.level_walls[screen] and [x, y+1] not in self.level_walls[screen]:
								self.tile_type = 23
						else:
							self.tile_type = 13
						self.map_list.append(BG.wall_tiles[self.tile_type])
						self.map_tiles[screen].append(BG.wall_tiles[self.tile_type])

					else:
						if [x-1, y] in self.level_walls[screen]:
							if [x, y-1] in self.level_walls[screen]:
								self.tile_type = 0
							elif [x, y+1] in self.level_walls[screen]:
								self.tile_type = 6
							else:
								self.tile_type = 3
						elif [x+1, y] in self.level_walls[screen]:
							if [x, y-1] in self.level_walls[screen]:
								self.tile_type = 2
							elif [x, y+1] in self.level_walls[screen]:
								self.tile_type = 8
							else:
								self.tile_type = 5
						elif [x, y-1] in self.level_walls[screen]:
							self.tile_type = 1
						elif [x, y+1] in self.level_walls[screen]:
							self.tile_type = 7
						else:
							self.tile_type = 4

						self.map_list.append(BG.floor_tiles[self.tile_type])
						self.map_tiles[screen].append(BG.floor_tiles[self.tile_type])

	def walls_update(self, level, Grid ):
		key = (level.screen_x, level.screen_y)
		self.walls = self.level_walls[key]
		Grid = pf.Grid(self.level_walls[key], 24, 24)


	def draw_collision(self, win, BG, width, height):
		win.fill( (150,150,150))
		for wall in self.walls: #Draws the walls 
			rect = pygame.Rect(wall[0] *self.tile, wall[1] *self.tile, self.tile, self.tile)
			pygame.draw.rect(win, (150,100,100), rect)

		if not BG.scroll:
			self.tile_screen = (BG.screen_x, BG.screen_y) #Updates screen after finish scroll

		self.count = 0

		for y in range(13): #Draw tiles 
			for x in range (17): #Tile Size
				if BG.scroll:
					if self.tile_screen[0] < BG.screen_x:#Screen move right
						win.blit(self.map_tiles[self.tile_screen][self.count], (BG.x+x*24,y*24)) #Current screen
						win.blit(self.map_tiles[(BG.screen_x, BG.screen_y)][self.count], (width+BG.x+x*24, y*24))
					elif self.tile_screen[0] > BG.screen_x: #Screen move left 
						win.blit(self.map_tiles[self.tile_screen][self.count], (width+BG.x +x*24,y*24)) #Current screen
						win.blit(self.map_tiles[(BG.screen_x, BG.screen_y)][self.count], (BG.x+x*24,y*24))
					elif self.tile_screen[1] < BG.screen_y: #Screen move down
						win.blit(self.map_tiles[self.tile_screen][self.count], (x*24,BG.y+y*24)) #Current screen
						win.blit(self.map_tiles[(BG.screen_x, BG.screen_y)][self.count], (x*24, height+BG.y+y*24))
					elif self.tile_screen[1] > BG.screen_y: #Screen move up 
						win.blit(self.map_tiles[self.tile_screen][self.count], (x*24,height+BG.y+y*24)) #Current screen
						win.blit(self.map_tiles[(BG.screen_x, BG.screen_y)][self.count], (x*24,BG.y+y*24))
				else:
					win.blit(self.map_tiles[self.tile_screen][self.count], (x*24,y*24))
				self.count += 1

	def draw_grid(self, win, width, height):
		for x in range (0, width, self.tile):
			pygame.draw.line(win, (20,20,20), (x, 0), (x, height))
		for y in range (0, height, self.tile):
			pygame.draw.line(win, (20,20,20), (0,y), (width,y))			

def Move_Direction(vector):
	##### Vector: (Left, Right, Front, Back, x, y, Distance)
	sqrt = 0.70
	sqrt2 = 1.40
	dictionary = {(1, 0): (0, 1, 0, 0, 1, 0, 1),
					(0, 1): (0, 0, 1, 0, 0, 1, 1),
					(-1, 0): (1, 0, 0, 0, -1, 0, 1),
					(0, -1): (0, 0, 0, 1, 0, -1, 1),
					(1, -1): (0, 1, 0, 1, sqrt, -sqrt, sqrt2),
					(1, 1): (0, 1, 1, 0, sqrt, sqrt, sqrt2),
					(-1, -1): (1, 0, 0, 1, -sqrt, -sqrt, sqrt2),
					(-1, 1): (1, 0, 1, 0, -sqrt, sqrt, sqrt2)}

	return dictionary[vector]

def Pathfinder(grid, unit, target, BG):
	TileSize = 24 
	if unit.wait <=  0 and  unit.screen == (BG.screen_x, BG.screen_y): 
		unit.path = []
		unit_cost = []
		unit.tracker = 0
		unit.distance = 0
		pos_1 = pf.vec(unit.x+TileSize/2, unit.y+TileSize/2)//TileSize #Start 
		pos_2 = pf.vec(target.x+TileSize/2, target.y+TileSize/2)//TileSize #End 
		path, cost = pf.a_star_search(grid, pos_2, pos_1) #Calculate possible moves
		current = pos_1 #Working variable for vectors

		while current != pos_2:
			if (current.x, current.y) in path:  
				temp = path[(current.x, current.y)] #Finds vector using "Current" node 
				unit.path.append(pf.vec2int(temp)) #Add vector to direction vector
			if (pos_1.x, pos_1.y) in cost:
				unit_cost = cost[(pos_1.x, pos_1.y)] #Adds cost for that vecto
			else:
				unit_cost = 15

			if (current.x, current.y) in path:
				current = current + path[(current.x, current.y)] #Advance "Current" to the next node
			else:
				break

		unit.wait = 40
		#dprint('The path is: ' + str(unit.path))
	else:
		
		unit.wait -= 1 
		if unit.path != []: #Apply pathfinding
			if unit.tracker<len(unit.path):#
				if unit.path[unit.tracker] != None:
					#if unit.race == 'Human': #Set unit direction
					unit.left = Move_Direction(unit.path[unit.tracker])[0]
					unit.right = Move_Direction(unit.path[unit.tracker])[1]
					unit.front = Move_Direction(unit.path[unit.tracker])[2]
					unit.back = Move_Direction(unit.path[unit.tracker])[3]
					unit.direction = unit.direct_dict[unit.path[unit.tracker]] 

					unit.distance += unit.speed
					unit.x += Move_Direction(unit.path[unit.tracker])[4]*unit.speed
					unit.y += Move_Direction(unit.path[unit.tracker])[5]*unit.speed							
					
					if unit.tracker<len(unit.path) and round(unit.distance) >= TileSize*Move_Direction(unit.path[unit.tracker])[6]:#Tally to next direction vector
						unit.distance = 0
						unit.tracker +=1 

def main():
	width = 408
	height = 312 
	win = pygame.display.set_mode((width, height)) # 17 x 13 tiles 
	#win = pygame.display.set_mode((408, 312)) # 17 x 13 tiles 
	pygame.init()

	Red_Guy = Characters(100, 150, 10, 20,  (255, 0, 0))
	Blue_Guy1 = Enemies(200, 125, 10, 20, (0, 0, 255), (0,0) )
	Blue_Guy2 = Enemies(600, 125, 10, 20, (0, 0, 255), (1,0) )
	Blue_Guy3 = Enemies(600, 525, 10, 20, (0, 0, 255), (1,1) )
	Blue_Guy4 = Enemies(200, 525, 10, 20, (0, 0, 255), (0,1) )

	enemies = [Blue_Guy1, Blue_Guy2, Blue_Guy3, Blue_Guy4]#
	BG = Background(1, width, height, 0,0)
	Tile = Tiles(24, BG)
	Grid = pf.Grid(Tile.level_walls[(1,0)], 24, 24)

	bullets = []

	while True:
		frames = 30
		clock=pygame.time.Clock()
		clock.tick(frames)

		for event in pygame.event.get(): #Exit game on red button
			if event.type == pygame.QUIT:
				return
		
		#Background Art
		BG.screen_change(win, Red_Guy, enemies)
		Tile.draw_collision(win, BG, width, height) #Draws the functional nodes with art 
#		BG.draw_bg(win) ## Pre-made BG
		Tile.walls_update(BG, Grid )
		Tile.draw_grid(win, width, height)
		#Player Objects
		if not BG.scroll:
			Move_Object(Red_Guy, height, width, BG, Tile)

		Shoot(Red_Guy) 
		Invulnerable(Red_Guy)
		Red_Guy.frames()
		win.blit(pygame.transform.flip(Red_Guy.sprites[math.floor(Red_Guy.frame)],Red_Guy.flip,0),(Red_Guy.x-11,Red_Guy.y-9))
		#Enemy Objects
		for enemy in enemies:
			if enemy.health>0:
				#Hunt(enemy, Red_Guy, width, height)
				Object_Collision(enemy, Red_Guy)
				enemy.frames()
				win.blit(pygame.transform.flip(enemy.sprites[math.floor(enemy.frame)],enemy.flip,0),(enemy.x-11,enemy.y-9))

			for bullet in Red_Guy.bullets:
				bullet.Move(win)
				Proj_Collision(Red_Guy, bullet, enemy)
				
			Screen_Scroll(Red_Guy, enemies, BG)
			Pathfinder(Grid, enemy, Red_Guy, BG)

		
		pygame.display.flip()

main()
