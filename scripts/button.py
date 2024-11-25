import pygame


class Button:
    def __init__(self, pos, size, color):
        self.pos = list(pos)
        self.size = size
        self.children = []
        self.color = color
        self.isMouseOver = False
    def addChildren(self, child):
        self.children.append(child)
        
    def rect(self):
        return pygame.Rect(self.pos, self.size)
    
    def update(self, mPos, offset):
        self.isMouseOver = False
        if self.rect().collidepoint([mPos[0], mPos[1] + offset - 75]):
            self.isMouseOver = True
            
    def render(self, surf, offset):
        for child in self.children:
            if child["type"] == "text":
                surf.blit(child["element"], (child["pos"][0], child["pos"][1] - offset))
            elif child["type"] == "rect":
                pygame.draw.rect(surf, child["color"], ((child["element"][0], child["element"][1] - offset), (child["element"].width, child["element"].height)))
                
        if self.isMouseOver:
            pygame.draw.line(surf, (0, 255, 0), (self.pos[0], self.pos[1] - offset), (self.pos[0] + self.size[0], self.pos[1] - offset))
            pygame.draw.line(surf, (0, 255, 0), (self.pos[0], self.pos[1] - offset + self.size[1]), (self.pos[0] + self.size[0], self.pos[1] - offset + self.size[1]))
            pygame.draw.line(surf, (0, 255, 0), (self.pos[0], self.pos[1] - offset), (self.pos[0], self.pos[1] - offset + self.size[1]))
            pygame.draw.line(surf, (0, 255, 0), (self.pos[0] + self.size[0] - 1, self.pos[1] - offset), (self.pos[0] + self.size[0] - 1, self.pos[1] - offset + self.size[1]))
            
        
    