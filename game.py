import pygame, sys, random, math
from scripts.entities import Player, Enemy
from scripts.utils import loadImage, loadImages, Animation
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.button import Button
import socketio

RENDER_SCALE = 2.0
SPAWNING_RATE = 50000

class Game():
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((800, 512))
        self.display = pygame.Surface((400, 256))
        self.funcSurf = pygame.Surface((300, self.screen.get_height()))
        self.surfRenderZone = pygame.Surface((300, self.screen.get_height() - 75))
        self.Clock = pygame.time.Clock()
        
        self.movement = [False, False]
        
        self.socket = socketio.Client()
        self.socket.connect("http://172.16.96.60:3000")

        self.otherPlayers = []
        
        self.assets = {
            "decor": loadImages("tiles/decor"),
            "grass": loadImages("tiles/grass"),
            "large_decor": loadImages("tiles/large_decor"),
            "stone": loadImages("tiles/stone"),
            "player": loadImage("entities/player.png"),
            "background": loadImage("background.png"),
            "clouds": loadImages("clouds"),
            "enemy/idle": Animation(loadImages("entities/enemy/idle"), imgDur = 6),
            "enemy/run": Animation(loadImages("entities/enemy/run"), imgDur = 4),
            "player/idle": Animation(loadImages("entities/player/idle"), imgDur = 6),
            "player/run": Animation(loadImages("entities/player/run"), imgDur = 4),
            "player/jump": Animation(loadImages("entities/player/jump")),
            "player/slide": Animation(loadImages("entities/player/slide")),
            "player/wall_slide": Animation(loadImages("entities/player/wall_slide")),
            "particles/leaf" : Animation(loadImages("particles/leaf"), imgDur = 12, loop = False),
            "particles/particle" : Animation(loadImages("particles/particle"), imgDur = 4, loop = False),
            "gun": loadImage("gun.png"),
            "shuriken": loadImage("shuriken.png"),
            "projectile": loadImage("projectile.png"),
            "spawners": loadImages("tiles/spawners"),
            "font/playerName": pygame.font.Font("data/font/Roboto-Bold.ttf", 14),
            "font/zone": pygame.font.Font("data/font/Roboto-Bold.ttf", 20),
            "font/zoneIndex": pygame.font.Font("data/font/Roboto-Bold.ttf", 25),
        }
        
        self.editorAssets = {
            "decor": loadImages("tiles/decor"),
            "grass": loadImages("tiles/grass"),
            "large_decor": loadImages("tiles/large_decor"),
            "stone": loadImages("tiles/stone"),
            "spawners": loadImages("tiles/spawners"),
        }

        self.clouds = Clouds(self.assets["clouds"], count = 16)
        self.player = Player(self, (50, 50), (8, 15))
        self.scoll = [0, 0]
        self.tilemap = Tilemap(self, tileSize = 16)
        self.loadLevel(0)     
        # self.tilemap = Tilemap(self, tileSize = 16)
        # editor/create maps
        self.editorMovement = [False, False, False, False]        
        self.tileList = list(self.editorAssets)
        self.tileGroup = 0
        self.tileVariant = 0
        self.clicking = False
        self.rightClicking = False
        self.shift = False
        self.onGrid = True
        self.sparks = []
        self.shurikens = []
        self.zones = []
        self.zoneBtns = []
        self.isRenderZone = False
        self.zoneScroll = 0
        
        self.mapSize = [] # left, right, bottom, top
        
        self.mapSize = self.tilemap.getMapSize()
        
        # socket.io event handlers
        self.socket.emit("getSID")
        @self.socket.on("serverSendSID")
        def onserverSendSID(SID):
            self.player.ID = SID
            self.socket.emit("login", {"player": self.player.toJson()})

        @self.socket.on("serverSend")
        def onserverSend(message):
            for id in message:
                if self.player.ID == message[id]["ID"]:
                    continue
                player = Player(self, (0, 0), (8, 15))
                player.fromJson(message[id])
                isAlready = False
                for otherPlayer in self.otherPlayers:
                    if otherPlayer.ID == player.ID:
                        isAlready = True
                        break
                if isAlready:
                    continue
                
                self.otherPlayers.append(player)

        @self.socket.on("updatedPlayer")
        def onupdatedPlayer(data):
            for otherPlayer in self.otherPlayers:
                if otherPlayer.ID == data["ID"]:
                    otherPlayer.fromJson(data)
                    break
                
        @self.socket.on("actionReceived")
        def onactionReceived(data):
            for otherPlayer in self.otherPlayers:
                if otherPlayer.ID in data:
                    otherPlayer.setAction(data[otherPlayer.ID])
                    break
        
        @self.socket.on("zonesReceived")
        def onzonesReceived(data):
            self.zones = data["zones"] #[zone index, number of players in zone]
            self.isRenderZone = True
            GAP = 40
            padding = 7
            y = 75
            for index, zone in enumerate(self.zones):
                btn = Button((0, y), (300, GAP), (0, 0, 0, 0))
                zoneIndexRender = self.assets["font/zoneIndex"].render(
                    str(index), True, (0, 0, 0, 255))
                zoneRender = self.assets["font/zone"].render(
                    str(zone[0]) + '/' + str(zone[1]), True, (0, 0, 0, 255))
                btn.addChildren(
                    {
                        "element": pygame.Rect(0, y, 300, GAP),
                        "type": "rect",
                        "color": (162, 165, 156, 255)
                    })
                btn.addChildren(
                    {
                        "element": pygame.Rect(0, y, 50,  GAP),
                        "type": "rect",
                        "color": (222, 159, 72, 255)
                    })
                btn.addChildren(
                    {
                        "element": zoneRender,
                        "type": "text",
                        "pos": (160 - zoneRender.get_width() / 2,
                                    y + zoneRender.get_height() / 2 - padding * 0.5)
                    })
                btn.addChildren(
                    {
                        "element": zoneIndexRender,
                        "type": "text",
                        "pos": (23 - zoneIndexRender.get_width() / 2,
                                    y + zoneIndexRender.get_height() / 2 - padding)
                    })
                self.zoneBtns.append(btn)
                y += GAP + 3
            
        @self.socket.on("userDisconnected")
        def onuserDisconnected(ID):
            for otherPlayer in self.otherPlayers.copy():
                if otherPlayer.ID == ID:
                    self.otherPlayers.remove(otherPlayer)
                    print("removed player", ID)
                    break
        
    def loadLevel(self, mapID):
        self.tilemap.load("data/maps/" + str(mapID) + ".json")
        
        self.leafSpawner = []
        self.enemies = []
        self.particles = []
        self.projectiles = []
        self.scoll = [0, 0]
        self.sparks = []
        
        for tree in self.tilemap.extract([("large_decor", 2)], keep = True):
            self.leafSpawner.append(pygame.Rect((4 + tree["pos"][0], 4 + tree["pos"][1]), (23, 13))) # get the top left of canopy of tree 
        
        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1)]):
            if spawner["variant"] == 0:
                self.player.pos = list(spawner["pos"])
            else:
                self.enemies.append(Enemy(self, spawner["pos"], (8, 15)))
                
    def run(self):  
        while True:
            self.display.blit(pygame.transform.scale(self.assets["background"], self.display.get_size()), (0, 0))
            mPos = pygame.mouse.get_pos()
            self.scoll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scoll[0]) / 30
            self.scoll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scoll[1]) / 5

            scrollRender = (int(self.scoll[0]), int(self.scoll[1]))
            if scrollRender[0] >= self.mapSize[1] - self.display.get_width() + self.tilemap.tileSize * 1.5:
                scrollRender = (int(self.mapSize[1] - self.display.get_width() + self.tilemap.tileSize * 1.5), scrollRender[1])
            if scrollRender[0] <= self.mapSize[0]:
                scrollRender = (self.mapSize[0], scrollRender[1])
            if scrollRender[1] >= self.mapSize[2] - self.display.get_height() + self.tilemap.tileSize:
                scrollRender = (scrollRender[0], self.mapSize[2] - self.display.get_height() + self.tilemap.tileSize)
            if scrollRender[1] <= self.mapSize[3] - self.display.get_height() - self.tilemap.tileSize * 2:
                scrollRender = (scrollRender[0], self.mapSize[3] - self.display.get_height() - self.tilemap.tileSize * 2)
            
            for rect in self.leafSpawner:
                if random.random() * SPAWNING_RATE < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    xVelocity = random.uniform(-0.15, -0.05)
                    yVelocity = random.uniform(0.15, 0.3)
                    self.particles.append(Particle(self, "leaf", pos,
                                                  velocity = [xVelocity, yVelocity],
                                                  frame = random.randint(0, len(self.assets["particles/leaf"].images))
                                                  ))
            
            self.clouds.update()
            self.clouds.render(self.display, offset=scrollRender)
            
            self.tilemap.render(self.display, offset = scrollRender)
            

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset = scrollRender)
                if kill:
                    self.enemies.remove(enemy)
            
            for otherPlayer in self.otherPlayers:
                otherPlayer.animation.update()
                otherPlayer.render(self.display, offset = scrollRender)
            
            for shuriken in self.shurikens.copy():
                kill = shuriken.update(self.tilemap, (0, 0))
                shuriken.render(self.display, offset = scrollRender)
                if kill:
                    self.shurikens.remove(shuriken)
            
            self.player.update(self.tilemap, mPos, ((self.movement[1] - self.movement[0]) * 2, 0), scrollRender)

            self.socket.emit("playerUpdate", self.player.toJson())
            
            self.player.render(self.display, offset = scrollRender)
            
            # projectile [[x, y], velocity vector, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets["projectile"]
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - scrollRender[0], projectile[0][1] - img.get_height() / 2 - scrollRender[1]))
                if self.tilemap.solidCheck(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360: # 360/60 = 6 secs
                    self.projectiles.remove(projectile)
                elif self.player.dashing < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.player.hp -= 1
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                            self.particles.append(
                                Particle(self, "particle", self.player.rect().center,
                                         velocity = [math.cos(angle + math.pi) * speed * 0.25,
                                                     math.sin(angle + math.pi) * speed * 0.5],
                                         frame = random.randint(0, 3)))
            
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.update()
                spark.render(self.display, offset = scrollRender)
                if kill:
                    self.sparks.remove(spark)
                    
            for paricle in self.particles.copy():
                kill = paricle.update()
                paricle.render(self.display, offset = scrollRender)
                if paricle.type == "leaf":
                    paricle.pos[0] += math.sin(paricle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(paricle)
                    
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.socket.disconnect()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.player.jump()
                    if event.key == pygame.K_SPACE:
                        self.player.dash()
                    if event.key == pygame.K_f:
                        self.player.thowShuriken()
                    if event.key == pygame.K_m:
                        self.socket.emit("getZones", self.player.location.split("/")[0])

                    if event.key == pygame.K_ESCAPE:
                        self.createMap()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 4 and self.isRenderZone:
                        self.zoneScroll -= 20
                    if event.button == 5 and self.isRenderZone:
                        self.zoneScroll += 20
                    if event.button == 1 and self.isRenderZone:
                        if self.funcSurf.get_width() <= mPos[0] <= self.screen.get_width():
                            self.isRenderZone = False
                            
            
            # player HUD
            # HP
            pygame.draw.rect(self.display, (128, 128, 128), (2, 5, 50, 10), border_radius = 3)
            pygame.draw.rect(self.display, (255, 255, 255), (4, 7, 46, 6), border_radius = 2)
            pygame.draw.rect(self.display, (255, 0, 0), (4, 7, int(46 * self.player.hp/self.player.maxHP), 6),
                            border_radius = 2)
            #  chakra
            pygame.draw.rect(self.display, (128, 128, 128), (2, 17, 45, 10), border_radius = 3)
            pygame.draw.rect(self.display, (255, 255, 255), (4, 19, 41, 6), border_radius = 2)
            pygame.draw.rect(self.display, (0, 0, 255), (4, 19, int(41 * self.player.chakra/self.player.maxChakra), 6),
                            border_radius = 2)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            
            for otherPlayer in self.otherPlayers:
                otherPlayer.renderName(self.screen, scrollRender)
            
            self.player.renderName(self.screen, scrollRender)
            
            if self.isRenderZone:
                if self.zoneScroll < 75:
                    self.zoneScroll = 75
                if self.zoneScroll > len(self.zoneBtns) * 43 - self.screen.get_height()//2 - 86:
                    self.zoneScroll = len(self.zoneBtns) * 43 - self.screen.get_height() // 2 - 86
                self.funcSurf.fill((128, 128, 128))
                self.surfRenderZone.fill((128, 128, 128))
                
                for btn in self.zoneBtns:
                    btn.update(mPos, self.zoneScroll)
                    btn.render(self.surfRenderZone, self.zoneScroll)
                    
                self.funcSurf.blit(self.surfRenderZone, (0, 80))
                self.screen.blit(self.funcSurf, (0, 0))
            pygame.display.update()
            self.Clock.tick(60)
    
           
    def createMap(self):
        while True:
            self.display.blit(pygame.transform.scale(self.assets["background"], self.display.get_size()), (0, 0))
            
            self.scoll[0] += (self.editorMovement[1] - self.editorMovement[0]) * 2
            self.scoll[1] += (self.editorMovement[3] - self.editorMovement[2]) * 2
            
            scrollRender = (int(self.scoll[0]), int(self.scoll[1]))
            self.tilemap.render(self.display, offset = scrollRender)
            
            currentTileImage = self.editorAssets[self.tileList[self.tileGroup]][self.tileVariant]
            
            mPos = pygame.mouse.get_pos()
            mPos = [mPos[0] / RENDER_SCALE, mPos[1] / RENDER_SCALE]
            tilePos = [int((mPos[0] + self.scoll[0]) // self.tilemap.tileSize), int((mPos[1] + self.scoll[1]) // self.tilemap.tileSize)]
            
            if not self.rightClicking:
                if self.onGrid:
                    self.display.blit(currentTileImage, (tilePos[0] * self.tilemap.tileSize - self.scoll[0], tilePos[1] * self.tilemap.tileSize - self.scoll[1]))
                else:
                    self.display.blit(currentTileImage, mPos)
            if self.clicking and self.onGrid:
                self.tilemap.tilemap[str(tilePos[0]) + ';' + str(tilePos[1])] = {
                    "type": self.tileList[self.tileGroup],
                    "variant": self.tileVariant,
                    "pos": tilePos,
                    }
            
            if self.rightClicking:
                tileLocation = str(tilePos[0]) + ';' + str(tilePos[1])
                if tileLocation in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tileLocation]
                for tile in self.tilemap.offgridTiles.copy():
                    tileImage = self.assets[tile["type"]][tile["variant"]]
                    tileRect = pygame.Rect(
                        tile["pos"][0] - self.scoll[0],
                        tile["pos"][1] - self.scoll[1],
                        tileImage.get_width(),
                        tileImage.get_height()
                        )
                    if tileRect.collidepoint(mPos):
                        self.tilemap.offgridTiles.remove(tile)
            
            self.display.blit(currentTileImage, (5, 5))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.onGrid:
                            self.tilemap.offgridTiles.append({
                                "type": self.tileList[self.tileGroup],
                                "variant": self.tileVariant,
                                "pos": (mPos[0] + self.scoll[0], mPos[1] + self.scoll[1]),
                            })
                    if event.button == 3:
                        self.rightClicking = True
                    
                    if self.shift:
                        if event.button == 4:
                            self.tileVariant = (self.tileVariant - 1) % len(self.editorAssets[self.tileList[self.tileGroup]])
                        if event.button == 5:
                            self.tileVariant = (self.tileVariant + 1) % len(self.editorAssets[self.tileList[self.tileGroup]])
                    else:
                        if event.button == 4:
                            self.tileGroup = (self.tileGroup - 1) % len(self.tileList)
                            self.tileVariant = 0
                        if event.button == 5:
                            self.tileGroup = (self.tileGroup + 1) % len(self.tileList)
                            self.tileVariant = 0             
                
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.rightClicking = False
                     
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.editorMovement[0] = True
                    if event.key == pygame.K_d:
                        self.editorMovement[1] = True
                    if event.key == pygame.K_w:
                        self.editorMovement[2] = True
                    if event.key == pygame.K_DOWN:
                        self.editorMovement[3] = True
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_g:
                        self.onGrid = not self.onGrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_RETURN:
                        for tree in self.tilemap.extract([("large_decor", 2)], keep = True):
                            self.leafSpawner.append(pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13))
                        for spawner in self.tilemap.extract([("spawners", 0), ("spawners", 1)]):
                            if spawner["variant"] == 0:
                                self.player.pos = list(spawner["pos"])
                            else:
                                self.enemies.append(Enemy(self, spawner["pos"], (8, 15)))
                        self.run()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.editorMovement[0] = False
                    if event.key == pygame.K_d:
                        self.editorMovement[1] = False
                    if event.key == pygame.K_w:
                        self.editorMovement[2] = False
                    if event.key == pygame.K_DOWN:
                        self.editorMovement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
                        
                        
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.Clock.tick(60)
             
Game().run()