import pygame, math

class Shuriken():
    def __init__(self, img, pos, velocity = (0, 0)):
        self.img = img
        self.img = pygame.transform.scale(self.img, (8, 8))
        self.velocity = list(velocity)
        self.angle = 0
        self.pos = list(pos)
        self.lifeTime = 180
        
        self.renderSurf = pygame.Surface((self.img.get_width(), self.img.get_height()))
        
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.img.get_width(), self.img.get_height())

    def update(self, tilemap, offset = (0, 0)):
        self.angle = (self. angle + 18) % 90
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.lifeTime = max (0, self.lifeTime - 1)
        
        return not self.lifeTime
        
    def render(self, surf, offset = (0, 0)):
        
        surf.blit(pygame.transform.rotate(self.img, self.angle), (self.rect().centerx - offset[0], self.rect().centery - offset[1]))
            