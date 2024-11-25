import pygame, json, math

AUTOTILE_MAP = {
    tuple(sorted([(1,0),(0,1)])):0,
    tuple(sorted([(1,0),(0,1),(-1,0)])):1,
    tuple(sorted([(-1,0),(0,1)])):2,
    tuple(sorted([(-1,0),(0,-1),(0,1)])):3,
    tuple(sorted([(-1,0),(0,-1)])):4,
    tuple(sorted([(-1,0),(0,-1),(1,0)])):5,
    tuple(sorted([(1,0),(0,-1)])):6,
    tuple(sorted([(1,0),(0,-1),(0,1)])):7,
    tuple(sorted([(1,0),(-1,0),(0,1),(0,-1)])):8,

}

NEIGHBOR_OFFSET = [(-1, 0), (-1, -1), (0, - 1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {"grass", "stone"}
AUTOTILE_TYPES = {"grass", "stone"}

class Tilemap:
    def __init__(self, game, tileSize = 16, path = None):
        self.game = game
        self.tileSize = tileSize
        self.tilemap = {}
        self.offgridTiles = []
        if path is not None:
            with open(path, 'r') as file:
                data = json.load(file)
                self.tilemap = data["tilemap"]
                self.offgridTiles = data["offgrid"]
                self.tileSize = data["tileSize"]
    
    def extract(self, idPair, keep = False):
        matches = []
        for tile in self.offgridTiles.copy():
            if (tile["type"], tile["variant"]) in idPair:
                matches.append(tile)
                if not keep:
                    self.offgridTiles.remove(tile)
        
        for loc in self.tilemap.copy():
            tile = self.tilemap[loc]
            if (tile["type"], tile["variant"]) in idPair:
                matches.append(tile.copy())
                matches[-1]["pos"] = matches[-1]["pos"].copy()
                matches[-1]["pos"][0] *= self.tileSize
                matches[-1]["pos"][1] *= self.tileSize
                if not keep:
                    del self.tilemap[loc]
        
        return matches
        
    def tileAround(self, pos):
        tiles = []
        tileLoc = (int(pos[0] // self.tileSize), int(pos[1] // self.tileSize))
        for offset in NEIGHBOR_OFFSET:
            checkLoc = str(tileLoc[0] + offset[0]) + ";" + str(tileLoc[1] + offset[1])
            if checkLoc in self.tilemap:
                tiles.append(self.tilemap[checkLoc])
        return tiles
    
    def physicsRectsAround(self, pos):
        rects = []
        for tile in self.tileAround(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile["pos"][0] * self.tileSize, tile["pos"][1] * self.tileSize, self.tileSize, self.tileSize))
        return rects
    
    def solidCheck(self, pos):
        tileLoc = str(int(pos[0] // self.tileSize)) + ';' + str(int(pos[1] // self.tileSize))
        if tileLoc in self.tilemap:
            if self.tilemap[tileLoc]["type"] in PHYSICS_TILES:
                return self.tilemap[tileLoc]
    
    
    def render(self, surf, offset = (0, 0)):
        for tile in self.offgridTiles:
            surf.blit(self.game.assets[tile["type"]][tile["variant"]], (tile["pos"][0] - offset[0], tile["pos"][1] - offset[1]))
        
        for x in range(offset[0] // self.tileSize, (offset[0] + surf.get_width()) // self.tileSize + 1):
            for y in range(offset[1] // self.tileSize, (offset[1] + surf.get_height()) // self.tileSize + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile["type"]][tile["variant"]], (tile["pos"][0] * self.tileSize - offset[0], tile["pos"][1] * self.tileSize - offset[1]))

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0,-1), (0,1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';'+ str(tile['pos'] [1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]


    def getMapSize(self):
        maxX = -math.inf
        maxY = -math.inf
        minX = math.inf
        minY = math.inf
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            maxX = max(tile["pos"][0] * self.tileSize, maxX)
            maxY = max(tile["pos"][1] * self.tileSize, maxY)
            minX = min(tile["pos"][0] * self.tileSize, minX)
            minY = min(tile["pos"][1] * self.tileSize, minY)
            
        for tile in self.offgridTiles:
            maxX = max(tile["pos"][0], maxX)
            maxY = max(tile["pos"][1], maxY)
            minX = min(tile["pos"][0], minX)
            minY = min(tile["pos"][1], minY)
            
        return [int(minX), int(maxX), int(maxY), int(minY)]

    # i/o functions 
    def save(self, path):
        with open(path, 'w') as f:
            json.dump({
                "tilemap": self.tilemap,
                "offgrid": self.offgridTiles,
                "size": self.tileSize
            }, f)
    
    def load(self, path):
        with open(path, 'r') as f:
            data = json.load(f)
            self.tilemap = data["tilemap"]
            self.offgridTiles = data["offgrid"]
            self.tileSize = data["tileSize"]
        # for loc in self.tilemap:
        #     tile = self.tilemap[loc]
        #     surf.blit(self.game.assets[tile["type"]][tile["variant"]], (tile["pos"][0] * self.tileSize - offset[0], tile["pos"][1] * self.tileSize - offset[1]))
            
