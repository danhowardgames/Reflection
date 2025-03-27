import pygame
import sys
from settings import *
from game import Game

class Main:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Ric 'n' Shay")
        self.clock = pygame.time.Clock()
        self.game = Game(self.screen)
        
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.game.handle_event(event)
            
            # Update
            dt = self.clock.tick(FPS) / 1000.0
            self.game.update(dt)
            
            # Draw
            self.screen.fill(BG_COLOR)
            self.game.draw()
            
            pygame.display.flip()

if __name__ == "__main__":
    main = Main()
    main.run() 