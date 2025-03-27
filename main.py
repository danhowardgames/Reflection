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
        # Key press tracking
        self.space_pressed = False
        self.space_just_pressed = False
        
    def run(self):
        while True:
            # Reset single-frame press states
            self.space_just_pressed = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                # Handle key press events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        print("SPACE key pressed down")
                        self.space_pressed = True
                        self.space_just_pressed = True
                        
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        print("SPACE key released")
                        self.space_pressed = False
                
                self.game.handle_event(event)
            
            # Update
            dt = self.clock.tick(FPS) / 1000.0
            
            # Get current keys state
            keys = pygame.key.get_pressed()
            
            # Update game with key states including our SPACE tracking
            self.game.update(dt, keys, self.space_just_pressed)
            
            # Draw
            self.screen.fill(BG_COLOR)
            self.game.draw()
            
            pygame.display.flip()

if __name__ == "__main__":
    main = Main()
    main.run() 