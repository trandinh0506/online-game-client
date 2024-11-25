class Particle:
    def __init__(self, game, pType, pos, velocity = [0, 0], frame = 0):
        self.game = game
        self.type = pType
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.animation = self.game.assets["particles/" + self.type].copy()
        self.animation.frame = frame
        
    def update(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.animation.update()
        
        return self.animation.done
    
    def render(self, surf, offset = (0, 0)):
        img = self.animation.img()
        surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))