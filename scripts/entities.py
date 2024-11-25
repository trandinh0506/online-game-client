import pygame, math, random
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.shuriken import Shuriken
class PhysicalEntity:
    def __init__(self, game, eType, pos, size):
        self.game = game
        self.type = eType
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "left": False, "right": False}
        
        self.action = ""
        self.animOffset = (-3, -3) # offset for padding of image
        self.flip = False
        self.setAction("idle")
        
        self.lastMovement = [0, 0]
        self.hp = 0
        self.maxHP = 0
        
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def setAction(self, action):
        if not "ID" in self.__dict__:
            self.ID = ""
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()
            return True
            
    def update(self, tilemap, movement = (0, 0)):
        self.collisions = {"up": False, "down": False, "left": False, "right": False}
        
        frameMovement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        self.pos[0] += frameMovement[0]
        entity_rect = self.rect()
        for rect in tilemap.physicsRectsAround(self.pos):
            if entity_rect.colliderect(rect):
                if frameMovement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frameMovement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x
                
        self.pos[1] += frameMovement[1]
        entity_rect = self.rect()
        for rect in tilemap.physicsRectsAround(self.pos):
            if entity_rect.colliderect(rect):
                if frameMovement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frameMovement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y
             
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True     
           
        self.lastMovement = movement
        
        self.velocity[1] = min(4, self.velocity[1] + 0.12)
        if self.collisions["up"] or self.collisions["down"]:
            self.velocity[1] = 0
        
        self.animation.update()
        
    def render(self, surf, offset = (0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.animOffset[0], int(self.pos[1]) - offset[1] + self.animOffset[1]))
        
 
class Enemy(PhysicalEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "enemy", pos, size)
        self.walking = 0
        self.shootCountDown = 0
    
    def update(self, tilemap, movement = (0, 0)):
                       
        if not self.shootCountDown:
            distance = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
            if (abs(distance[1]) < 16):
                self.walking = 0
                if self.flip and distance[0] < 0:
                    self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -3.5, 0])
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                if not self.flip and distance[0] > 0:
                    self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 3.5, 0])
                    for i in range(4):
                        self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
                self.shootCountDown = 210
        if self.walking:
            if tilemap.solidCheck((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions["left"] or self.collisions["right"]:
                    self.flip = not self.flip
                else:
                    movement = [movement[0] + (-0.5 if self.flip else 0.5), movement[1]]
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)

        elif random.random() < 0.1:
            self.walking = random.randint(30, 120)
            
        self.shootCountDown = max(0, self.shootCountDown - 1)
        super().update(tilemap, movement = movement)
        if movement[0] != 0:
            self.setAction("run")
        else:
            self.setAction("idle")
        
        if self.game.player.dashing >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
                    self.game.particles.append(
                        Particle(self.game, "particle", self.rect().center,
                                    velocity = [math.cos(angle + math.pi) * speed * 0.25,
                                                math.sin(angle + math.pi) * speed * 0.5],
                                    frame = random.randint(0, 3)))
                self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))
                return True
                
    def render(self, surf, offset = (0, 0)):
        super().render(surf, offset = offset)
        margin = 2
        if self.flip:
            surf.blit(
                pygame.transform.flip(
                    self.game.assets["gun"], True, False),
                    (self.rect().centerx - self.game.assets["gun"].get_width() - offset[0] - margin,
                    self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets["gun"], (self.rect().centerx - offset[0] + margin, self.rect().centery - offset[1]))
        
class Player(PhysicalEntity):
    def __init__(self, game, pos, size):
        super() .__init__(game, "player", pos, size)
        self.airTime = 0
        self.jumps = 2
        self.wallSlide = False
        self.dashing = 0
        self.angle = 0
        self.mPos = (0, 0)
        self.dashAngle = 0
        self.dashMousePos = (0, 0)
        self.hp = 10
        self.maxHP = 10
        self.name = "Định Đz 1"
        self.movement = [0, 0]
        self.shurikenCountdown = 0
        self.power = 100
        self.chakra = 10
        self.maxChakra = 10
        self.recoverChakraRate = 1
        self.baseRecoverChakraSpeed = 0.005
        self.recoverChakraSpeed = self.baseRecoverChakraSpeed * self.recoverChakraRate
        self.dashChakraConsum = 0.7
        self.location = "map1/0"
        
    def update(self, tilemap, mPos, movement = (0,0), offset = (0, 0)):
        super().update(tilemap, movement=movement)
        if self.pos[0] > self.game.mapSize[1] + self.game.tilemap.tileSize / 2:
            self.pos[0] = self.game.mapSize[1] + self.game.tilemap.tileSize / 2
        elif self.pos[0] < self.game.mapSize[0]:
            self.pos[0] = self.game.mapSize[0]
        elif self.pos[1] > self.game.mapSize[2]:
            self.pos[1] = self.game.mapSize[2]
            self.collisions["down"] = True
            self.velocity[1] = 0
        elif self.pos[1] < self.game.mapSize[3] - self.game.display.get_height():
            self.pos[1] = self.game.mapSize[3] - self.game.display.get_height()
            
        self.angle = math.atan2(mPos[1] - (self.pos[1] - offset[1] + self.animOffset[1] + self.size[1] / 2) * 2,
                                mPos[0] - (self.pos[0] - offset[0] + self.animOffset[0] + self.size[0] / 2) * 2 
                                )
        self.chakra = min(self.maxChakra, self.chakra + self.recoverChakraSpeed)
        self.movement = movement
        self.mPos = mPos
        self.airTime += 1
        if self.collisions["down"]:
            self.airTime = 0
            self.jumps = 2
        
        self.wallSlide = False
        if (self.collisions["right"] or self.collisions["left"]) and self.airTime > 4:
            self.wallSlide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            
            self.flip = self.collisions["left"]
            self.setAction("wall_slide")
        if not self.wallSlide:  
            if self.airTime > 4:
                self.setAction("jump")
            elif self.movement[0] != 0:
                self.setAction("run")
            else:
                self.setAction("idle")

        self.shurikenCountdown = max(0, self.shurikenCountdown - 1)
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing > 50:
            velocity =  min(12,
                        math.sqrt(
                        (self.dashMousePos[0] - (self.pos[0] - offset[0] + self.animOffset[0]) * 2)**2 +
                        (self.dashMousePos[1] - (self.pos[1] - offset[1] + self.animOffset[1]) * 2)**2)/10)
            
            self.velocity[0] = math.cos(self.dashAngle) * velocity
            self.velocity[1] = math.sin(self.dashAngle) * velocity
            self.flip = self.velocity[0] < 0
            if self.dashing == 51:
                self.velocity[0] *= 0.1
                self.velocity[1] *= 0.1
        
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
            
    def render(self, surf, offset = (0, 0)):
        if self.dashing in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(self.game, "particle", self.rect().center,
                             velocity = pvelocity, frame = random.randint(0, 3)))
        if self.dashing > 50:
            velocity = 12
            self.game.particles.append(
                    Particle(self.game, "particle", self.rect().center,
                    velocity = [ math.cos(self.dashAngle) * velocity * 0.2, math.sin(self.dashAngle) * velocity * 0.2],
                    frame = random.randint(0, 3)))
        
        if self.dashing <= 50:
            super().render(surf, offset = offset)            
    
    def renderName(self, surf, offset):
        if self.dashing <= 50:
            text = self.game.assets["font/playerName"].render(self.name, True, (255, 255, 255))
            surf.blit(text, ((self.rect().centerx - offset[0] + self.animOffset[0]) * 2 - text.get_width() // 2  + 4, int(self.rect().top - offset[1]) * 2 - text.get_height()))
    
    def setAction(self, action):
        if super().setAction(action) and self.ID != "" and self.game.player.ID == self.ID:
            super().setAction(action)
            self.game.socket.emit("setAction", {self.ID: self.action})
            
    def jump(self):
        if self.wallSlide:
            if self.flip and self.lastMovement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.airTime = 5
                self.jumps = max(0, self.jumps - 1)
            elif not self.flip and self.lastMovement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.airTime = 5
                self.jumps = max(0, self.jumps - 1)
                
        elif self.jumps:
            self.airTime = 5
            if self.jumps == 2:
                self.velocity[1] -= 2.5
            elif self.jumps == 1:
                self.velocity[1] -= 3
            self.jumps -= 1
            
    def dash(self):
        dashTime = 60
        if not self.dashing and self.chakra >= self.dashChakraConsum:
            self.dashing = dashTime
            self.dashAngle = self.angle
            self.dashMousePos = self.mPos
            self.chakra -= self.dashChakraConsum
    
    def thowShuriken(self):
        if not self.shurikenCountdown:
            self.shurikenAngle = self.angle
            
            self.flip = abs(math.degrees(self.shurikenAngle)) > 90
            
            self.shurikenCountdown = 60
            speed = 1
            self.game.shurikens.append(
                Shuriken(self.game.assets["shuriken"], self.rect().center,
                         [math.cos(self.shurikenAngle) * speed, math.sin(self.shurikenAngle) * speed])
            )

    def fromJson(self, json):
        self.name                   = json["name"]
        self.ID                     = json["ID"]
        self.hp                     = json["hp"]
        self.maxHP                  = json["maxHP"]
        self.pos                    = json["pos"]
        self.wallSlide              = json["wallSlide"]
        self.velocity               = json["velocity"]
        self.jumps                  = json["jumps"]
        self.dashing                = json["dashing"]
        self.collisions             = json["collisions"]
        self.lastMovement           = json["lastMovement"]
        self.size                   = json["size"]
        self.flip                   = json["flip"]
        self.airTime                = json["airTime"]
        self.angle                  = json["angle"]
        self.dashMousePos           = json["dashMousePos"]
        self.dashAngle              = json["dashAngle"]
        self.movement               = json["movement"]
        self.power                  = json["power"]
        self.maxChakra               = json["maxChakra"]
        self.baseRecoverChakraSpeed = json["baseRecoverChakraSpeed"]
        self.chakra                 = json["chakra"]
        self.recoverChakraRate      = json["recoverChakraRate"]
        
    def toJson(self):
        json = {
            "name"                  : self.name,
            "ID"                    : self.ID,
            "hp"                    : self.hp,
            "maxHP"                 : self.maxHP,
            "pos"                   : self.pos,
            "wallSlide"             : self.wallSlide,
            "velocity"              : self.velocity,
            "jumps"                 : self.jumps,
            "dashing"               : self.dashing,
            "collisions"            : self.collisions,
            "lastMovement"          : self.lastMovement,
            "size"                  : self.size,
            "flip"                  : self.flip,
            "airTime"               : self.airTime,
            "angle"                 : self.angle,
            "dashMousePos"          : self.dashMousePos,
            "dashAngle"             : self.dashAngle,
            "movement"              : self.movement,
            "power"                 : self.power,
            "maxChakra"             : self.maxChakra,
            "chakra"                : self.chakra,
            "baseRecoverChakraSpeed": self.baseRecoverChakraSpeed,
            "recoverChakraRate"     : self.recoverChakraRate,
        }
        
        return json
        