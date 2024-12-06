import pygame
import random
import json
import os
import asyncio


pygame.init()


GRID_SIZE = 10
CELL_SIZE = 50
MARGIN = 2
SHAPE_CELL_SIZE = 30
SHAPE_MARGIN = 2


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 100, 255)
LIGHT_BLUE = (100, 200, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
PURPLE = (200, 100, 255)


GRID_PIXELS = GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN
WINDOW_WIDTH = GRID_PIXELS
WINDOW_HEIGHT = GRID_PIXELS + 200  
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Grid Block Game")


SHAPE_PATTERNS = [
    
    [[False, False, False],
     [False, True, False],
     [False, False, False]],
    
    
    [[True, True, True],
     [True, True, True],
     [True, True, True]],
     
    
    [[True, False, False],
     [True, False, False],
     [True, True, True]],
     
    
    [[True, False, False],
     [True, True, False],
     [True, False, False]],
     
    
    [[False, False, False],
     [True, True, False],
     [False, False, False]],
     
    
    [[True, True, False],
     [False, True, True],
     [False, False, False]],
     
    
    [[False, False, False],
     [True, False, False],
     [True, True, False]],
     
    
    [[False, False, False],
     [True, True, True],
     [False, False, False]],
     
    
    [[True, True, False],
     [True, True, True],
     [False, False, False]]
]

class Shape:
    def __init__(self, pattern):
        self.pattern = pattern
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
    def rotate(self):
        size = len(self.pattern)
        rotated = [[False] * size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                rotated[j][size-1-i] = self.pattern[i][j]
        self.pattern = rotated

class Game:
    def __init__(self):
        self.grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.shapes = []
        self.score = 0
        self.high_score = self.load_high_score()
        self.score_animation = None
        self.score_animation_time = 0
        self.game_over = False
        self.generate_shapes()

    def load_high_score(self):
        try:
            if os.path.exists('high_score.json'):
                with open('high_score.json', 'r') as f:
                    return json.load(f)['high_score']
        except:
            pass
        return 0

    def save_high_score(self):
        with open('high_score.json', 'w') as f:
            json.dump({'high_score': self.high_score}, f)

    def normalize_shape_position(self, shape, grid_x, grid_y):
        
        min_x = float('inf')
        min_y = float('inf')
        for y in range(len(shape.pattern)):
            for x in range(len(shape.pattern[y])):
                if shape.pattern[y][x]:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
        return grid_x - min_x, grid_y - min_y

    def is_game_over(self):
        """Check if any shape can be placed anywhere on the grid"""
        def can_place_at_position(shape, x, y):
            pattern = shape.pattern
            for py in range(len(pattern)):
                for px in range(len(pattern[py])):
                    if pattern[py][px]:
                        new_x, new_y = x + px, y + py
                        if (new_x < 0 or new_y < 0 or 
                            new_x >= GRID_SIZE or new_y >= GRID_SIZE or
                            self.grid[new_y][new_x]):
                            return False
            return True

        
        for shape in self.shapes:
            
            can_place = False
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if can_place_at_position(shape, x, y):
                        can_place = True
                        break
                if can_place:
                    break
                    
            
            if not can_place:
                return True
                
        return False

    def can_place_shape(self, shape, grid_x, grid_y):
        
        grid_x, grid_y = self.normalize_shape_position(shape, grid_x, grid_y)
            
        pattern = shape.pattern
        for y in range(len(pattern)):
            for x in range(len(pattern[y])):
                if pattern[y][x]:
                    new_x, new_y = grid_x + x, grid_y + y
                    if (new_x < 0 or new_y < 0 or 
                        new_x >= GRID_SIZE or new_y >= GRID_SIZE or
                        self.grid[new_y][new_x]):
                        return False
        return True

    def generate_shapes(self):
        self.shapes = []
        weighted_indices = (
            [0, 1] +  
            [i for i in range(2, len(SHAPE_PATTERNS)) for _ in range(4)]  
        )
        
        for _ in range(3):
            pattern_idx = random.choice(weighted_indices)
            pattern = [row[:] for row in SHAPE_PATTERNS[pattern_idx]]
            shape = Shape(pattern)
            if pattern_idx > 1:  
                for _ in range(random.randint(0, 3)):
                    shape.rotate()
            self.shapes.append(shape)
        
        
        if self.is_game_over():
            self.game_over = True

    def place_shape(self, shape, grid_x, grid_y):
        
        grid_x, grid_y = self.normalize_shape_position(shape, grid_x, grid_y)
        
        pattern = shape.pattern
        for y in range(len(pattern)):
            for x in range(len(pattern[y])):
                if pattern[y][x]:
                    self.grid[grid_y + y][grid_x + x] = True
        
        self.check_lines()
        self.shapes.remove(shape)

        
        if self.is_game_over():
            print("Game Over - No valid moves remaining!")
            self.game_over = True
            return
        
        
        if not self.shapes:
            self.generate_shapes()
            
            if self.is_game_over():
                print("Game Over - New shapes cannot be placed!")
                self.game_over = True

    def check_lines(self):
        lines_cleared = 0
        
        
        for y in range(GRID_SIZE):
            if all(self.grid[y]):
                self.grid[y] = [False] * GRID_SIZE
                lines_cleared += 1
        
        
        for x in range(GRID_SIZE):
            if all(row[x] for row in self.grid):
                for y in range(GRID_SIZE):
                    self.grid[y][x] = False
                lines_cleared += 1
        
        if lines_cleared > 0:
            base_score = lines_cleared * 100
            multiplier = lines_cleared
            total_score = base_score * multiplier
            
            self.score += total_score
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            
            self.score_animation = {
                'score': total_score,
                'multiplier': multiplier,
                'y': WINDOW_HEIGHT // 4
            }
            self.score_animation_time = pygame.time.get_ticks()

    def draw(self):
        SCREEN.fill(WHITE)
        
        
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(
                    x * (CELL_SIZE + MARGIN) + MARGIN,
                    y * (CELL_SIZE + MARGIN) + MARGIN,
                    CELL_SIZE, CELL_SIZE
                )
                pygame.draw.rect(SCREEN, BLUE if self.grid[y][x] else GRAY, rect)

        
        shape_start_y = GRID_PIXELS + 50
        for i, shape in enumerate(self.shapes):
            if not shape.dragging:
                shape_x = i * (3 * (SHAPE_CELL_SIZE + SHAPE_MARGIN) + 50) + 50
                shape_y = shape_start_y
                
                for y in range(len(shape.pattern)):
                    for x in range(len(shape.pattern[y])):
                        if shape.pattern[y][x]:
                            rect = pygame.Rect(
                                shape_x + x * (SHAPE_CELL_SIZE + SHAPE_MARGIN),
                                shape_y + y * (SHAPE_CELL_SIZE + SHAPE_MARGIN),
                                SHAPE_CELL_SIZE, SHAPE_CELL_SIZE
                            )
                            pygame.draw.rect(SCREEN, BLUE, rect)

        
        for shape in self.shapes:
            if shape.dragging:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - shape.offset_x) // (CELL_SIZE + MARGIN)
                grid_y = (mouse_y - shape.offset_y) // (CELL_SIZE + MARGIN)
                
                
                norm_x, norm_y = self.normalize_shape_position(shape, grid_x, grid_y)
                for y in range(len(shape.pattern)):
                    for x in range(len(shape.pattern[y])):
                        if shape.pattern[y][x]:
                            screen_x = norm_x * (CELL_SIZE + MARGIN) + x * (CELL_SIZE + MARGIN) + MARGIN
                            screen_y = norm_y * (CELL_SIZE + MARGIN) + y * (CELL_SIZE + MARGIN) + MARGIN
                            rect = pygame.Rect(screen_x, screen_y, CELL_SIZE, CELL_SIZE)
                            color = LIGHT_BLUE if self.can_place_shape(shape, grid_x, grid_y) else RED
                            pygame.draw.rect(SCREEN, color, rect)

        
        font = pygame.font.SysFont(None, 36)
        high_score_text = font.render(f'High Score: {self.high_score}', True, PURPLE)
        score_text = font.render(f'Score: {self.score}', True, BLUE)
        high_score_rect = high_score_text.get_rect()
        score_rect = score_text.get_rect()
        total_width = high_score_rect.width + score_rect.width + 20  
        start_x = (WINDOW_WIDTH - total_width) // 2
        SCREEN.blit(high_score_text, (start_x, 10))
        SCREEN.blit(score_text, (start_x + high_score_rect.width + 20, 10))

        
        if self.score_animation:
            current_time = pygame.time.get_ticks()
            if current_time - self.score_animation_time < 700:  
                score_font = pygame.font.SysFont(None, 48)
                score_text = font.render(
                    f'+{self.score_animation["score"]} (×{self.score_animation["multiplier"]})',
                    True, GREEN
                )
                text_rect = score_text.get_rect(center=(WINDOW_WIDTH//2, self.score_animation['y']))
                SCREEN.blit(score_text, text_rect)
                self.score_animation['y'] -= 2
            else:
                self.score_animation = None

        
        if self.game_over:
            font = pygame.font.SysFont(None, 72)
            game_over_text = font.render('GAME OVER', True, RED)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            
            
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(128)
            SCREEN.blit(overlay, (0, 0))
            
            
            SCREEN.blit(game_over_text, text_rect)

        pygame.display.flip()

async def main():
    game = Game()
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            
            if not game.game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = event.pos
                    shape_start_y = GRID_PIXELS + 50
                    
                    
                    for shape in game.shapes:
                        if not shape.dragging:
                            shape_idx = game.shapes.index(shape)
                            shape_x = shape_idx * (3 * (SHAPE_CELL_SIZE + SHAPE_MARGIN) + 50) + 50
                            shape_y = shape_start_y
                            
                            
                            shape_width = len(shape.pattern[0]) * (SHAPE_CELL_SIZE + SHAPE_MARGIN)
                            shape_height = len(shape.pattern) * (SHAPE_CELL_SIZE + SHAPE_MARGIN)
                            if (shape_x <= mouse_x <= shape_x + shape_width and
                                shape_y <= mouse_y <= shape_y + shape_height):
                                shape.dragging = True
                                shape.offset_x = mouse_x - shape_x
                                shape.offset_y = mouse_y - shape_y
                                break
                                
                elif event.type == pygame.MOUSEBUTTONUP:
                    for shape in game.shapes:
                        if shape.dragging:
                            mouse_x, mouse_y = event.pos
                            grid_x = (mouse_x - shape.offset_x) // (CELL_SIZE + MARGIN)
                            grid_y = (mouse_y - shape.offset_y) // (CELL_SIZE + MARGIN)
                            
                            if game.can_place_shape(shape, grid_x, grid_y):
                                game.place_shape(shape, grid_x, grid_y)
                            shape.dragging = False
        
        game.draw()
        clock.tick(60)

    pygame.quit()
    await asyncio.sleep(0)

if __name__ == '__main__':
    asyncio.run(main())