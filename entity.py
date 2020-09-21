import tcod as libtcod

import math

from render_functions import RenderOrder


class Entity:
    """
    a generic object to represent players, enemies, items, etc.
    """
    def __init__(self, x, y, char, color, name, blocks=False, render_order=RenderOrder.CORPSE, fighter=None, ai=None, item=None, inventory=None, stairs=None, level=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.render_order = render_order
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.stairs = stairs
        self.level = level

        if self.fighter:
            self.fighter.owner = self

        if self.ai:
            self.ai.owner = self

        if self.item:
            self.item.owner = self

        if self.inventory:
            self.inventory.owner = self
        
        if self.stairs:
            self.stairs.owner = self
        
        if self.level:
            self.level.owner = self

    def move(self, dx, dy):
        #move the entity by a given amount
        self.x += dx
        self.y += dy
    
    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        if not (game_map.is_blocked(self.x + dx, self.y + dy) or get_blocking_entities_at_location(entities, self.x + dx, self.y + dy)):
            self.move(dx, dy)
    
    def move_astar(self, target, entities, game_map):
        #create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(game_map.width, game_map.height)

        #scan the current map each turn and set all the walls as unwalkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                libtcod.map_set_properties(fov, x1, y1, not game_map.tiles[x1][y1].block_sight, not game_map.tiles[x1][y1].blocked)

        #scan all the objects to see if there are objects that must be navigated around
        #check also that the object isn't self or the target so that the start and end points are free
        #the AI class handles the situation if self is next t the target so it will not use this A* function anyway
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                #set the tile as a wall so it must be navigated around
                libtcod.map_set_properties(fov, entity.x, entity.y, True, False)
        
        #allocate a A* path
        #the 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
        my_path = libtcod.path_new_using_map(fov, 1.41)

        #compute the path between self's coordinates and the targets coordinates
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        #check if the path exists and in this case, also if it is shorter than 25 tiles
        #the path size matters if you want the monster to use alternativelonger paths (ex. through other rooms if the player is in a corridor)
        #it makes sense to keep the path size relatively low to keep the monsters from running around the map if there's an alternative path really far away
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            #find the next coordinates in the computed full path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                #set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            #keep the old move function as backup so that if there are no paths (for example another monster blocks a tunnel)
            #it will still try to move towards the player (closer to the opening)
            self.move_towards(target.x, target.y, game_map, entities)

            #delete the path to free memeory
        libtcod.path_delete(my_path) 

    def distance_to(self, other):
        dx = other.x - self.x 
        dy = other.y - self.y 
        return math.sqrt(dx ** 2 + dy ** 2)

    def distance(self, x, y):
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None