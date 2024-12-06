import pygame
import random
import json
import os
import asyncio

pygame.init()
pygame.mixer.init()

# Constants
GRID_SIZE = 10
CELL_SIZE = 50
MARGIN = 2
SHAPE_CELL_SIZE = 30
SHAPE_MARGIN = 2
SCORE_AREA_HEIGHT = 100  # Extra space at top for scores

# Window calculation
GRID_PIXELS = GRID_SIZE * (CELL_SIZE + MARGIN) + MARGIN
WINDOW_WIDTH = GRID_PIXELS
WINDOW_HEIGHT = SCORE_AREA_HEIGHT + GRID_PIXELS + 200
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Grid Block Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 100, 255)
LIGHT_BLUE = (100, 200, 255)
RED = (255, 100, 100)
GREEN = (100, 255, 100)
PURPLE = (200, 100, 255)

# Block colors for shapes
BLOCK_COLORS = [
    (0, 100, 255),   # BLUE
    (210, 45, 45),   # REDBLOCK
    (237, 174, 18),  # YELLOWBLOCK
    (47, 207, 65)    # GREENBLOCK
]

# Load sounds
place_sound = pygame.mixer.Sound('build/place.mp3')
hover_sound = pygame.mixer.Sound('build/hovergrid.mp3')
cheer_sound = pygame.mixer.Sound('build/cheer.mp3')
highscore_sound = pygame.mixer.Sound('build/highscore.mp3')
score_sound = pygame.mixer.Sound('build/score.mp3')

# Shape patterns
SHAPE_PATTERNS = [
    # Single cell
    [[False, False, False],
     [False, True, False],
     [False, False, False]],
    
    # 3x3 solid block
    [[True, True, True],
     [True, True, True],
     [True, True, True]],
     
    # L shape
    [[True, False, False],
     [True, False, False],
     [True, True, True]],
     
    # Modified L shape
    [[True, False, False],
     [True, True, False],
     [True, False, False]],
     
    # Right edge
    [[False, False, False],
     [True, True, False],
     [False, False, False]],
     
    # Diagonal 2
    [[True, True, False],
     [False, True, True],
     [False, False, False]],
     
    # Corner shape
    [[False, False, False],
     [True, False, False],
     [True, True, False]],
     
    # Middle horizontal line
    [[False, False, False],
     [True, True, True],
     [False, False, False]],
     
    # T shape
    [[True, True, False],
     [True, True, True],
     [False, False, False]]
]

class Shape:
    def __init__(self, pattern, color):
        self.pattern = pattern
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.color = color

    def rotate(self):
        size = len(self.pattern)
        rotated = [[False]*size for _ in range(size)]
        for i in range(size):
            for j in range(size):
                rotated[j][size-1-i] = self.pattern[i][j]
        self.pattern = rotated

class Game:
    def __init__(self):
        # Grid now stores either False or a (r,g,b) color
        self.grid = [[False]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.shapes = []
        self.score = 0
        self.high_score = self.load_high_score()
        self.score_animation = None
        self.score_animation_time = 0
        self.game_over = False

        # Hover logic
        self.last_hover_grid_x = None
        self.last_hover_grid_y = None
        self.currently_hovering_grid = False

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
        if len(self.shapes) == 0:
            # No shapes means we wait until generate_shapes()
            return False

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

        # Check if all shapes fail to place
        for shape in self.shapes:
            can_place_this_shape = False
            for yy in range(GRID_SIZE):
                for xx in range(GRID_SIZE):
                    if can_place_at_position(shape, xx, yy):
                        can_place_this_shape = True
                        break
                if can_place_this_shape:
                    break
            if can_place_this_shape:
                # Found a shape that can be placed, not game over
                return False
        # No shape can be placed
        return True

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
            color = random.choice(BLOCK_COLORS)
            shape = Shape(pattern, color)
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
                    self.grid[grid_y + y][grid_x + x] = shape.color

        place_sound.play()
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
        
        # Check rows
        for y in range(GRID_SIZE):
            if all(self.grid[y][x] != False for x in range(GRID_SIZE)):
                for x in range(GRID_SIZE):
                    self.grid[y][x] = False
                lines_cleared += 1
        
        # Check columns
        for x in range(GRID_SIZE):
            if all(self.grid[y][x] != False for y in range(GRID_SIZE)):
                for y in range(GRID_SIZE):
                    self.grid[y][x] = False
                lines_cleared += 1
        
        if lines_cleared > 0:
            base_score = lines_cleared * 100
            multiplier = lines_cleared
            total_score = base_score * multiplier
            
            self.score += total_score
            new_highscore = False
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
                new_highscore = True
            
            if new_highscore:
                highscore_sound.play()
            
            if multiplier > 1:
                cheer_sound.play()
            else:
                # single line/column clear
                if not new_highscore:
                    score_sound.play()

            self.score_animation = {
                'score': total_score,
                'multiplier': multiplier,
                'y': WINDOW_HEIGHT // 4
            }
            self.score_animation_time = pygame.time.get_ticks()

    def draw(self):
        SCREEN.fill(WHITE)

        # Draw scores at top
        font = pygame.font.SysFont(None, 36)
        high_score_text = font.render(f'High Score: {self.high_score}', True, PURPLE)
        score_text = font.render(f'Score: {self.score}', True, BLUE)
        high_score_rect = high_score_text.get_rect()
        score_rect = score_text.get_rect()
        total_width = high_score_rect.width + score_rect.width + 20
        start_x = (WINDOW_WIDTH - total_width) // 2
        SCREEN.blit(high_score_text, (start_x, 10))
        SCREEN.blit(score_text, (start_x + high_score_rect.width + 20, 10))

        # Draw grid shifted down by SCORE_AREA_HEIGHT
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                cell_val = self.grid[y][x]
                cell_color = cell_val if cell_val else GRAY
                rect = pygame.Rect(
                    x * (CELL_SIZE + MARGIN) + MARGIN,
                    y * (CELL_SIZE + MARGIN) + MARGIN + SCORE_AREA_HEIGHT,
                    CELL_SIZE, CELL_SIZE
                )
                pygame.draw.rect(SCREEN, cell_color, rect)

        # Draw available shapes below the grid
        shape_start_y = SCORE_AREA_HEIGHT + GRID_PIXELS + 50
        for i, shape in enumerate(self.shapes):
            if not shape.dragging:
                shape_x = i * (3 * (SHAPE_CELL_SIZE + SHAPE_MARGIN) + 50) + 50
                shape_y = shape_start_y
                for yy in range(len(shape.pattern)):
                    for xx in range(len(shape.pattern[yy])):
                        if shape.pattern[yy][xx]:
                            rect = pygame.Rect(
                                shape_x + xx * (SHAPE_CELL_SIZE + SHAPE_MARGIN),
                                shape_y + yy * (SHAPE_CELL_SIZE + SHAPE_MARGIN),
                                SHAPE_CELL_SIZE, SHAPE_CELL_SIZE
                            )
                            pygame.draw.rect(SCREEN, shape.color, rect)

        # Handle hover sound and draw dragged shapes
        hover_sound_should_play = False
        for shape in self.shapes:
            if shape.dragging:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = (mouse_x - shape.offset_x) // (CELL_SIZE + MARGIN)
                grid_y = (mouse_y - shape.offset_y - SCORE_AREA_HEIGHT) // (CELL_SIZE + MARGIN)

                norm_x, norm_y = self.normalize_shape_position(shape, grid_x, grid_y)
                can_place = self.can_place_shape(shape, grid_x, grid_y)
                for yy in range(len(shape.pattern)):
                    for xx in range(len(shape.pattern[yy])):
                        if shape.pattern[yy][xx]:
                            screen_x = norm_x * (CELL_SIZE + MARGIN) + xx * (CELL_SIZE + MARGIN) + MARGIN
                            screen_y = norm_y * (CELL_SIZE + MARGIN) + yy * (CELL_SIZE + MARGIN) + MARGIN + SCORE_AREA_HEIGHT
                            rect = pygame.Rect(screen_x, screen_y, CELL_SIZE, CELL_SIZE)
                            color = LIGHT_BLUE if can_place else RED
                            pygame.draw.rect(SCREEN, color, rect)

                # Check hover logic
                in_grid = (0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE)
                if in_grid:
                    if (not self.currently_hovering_grid or 
                        grid_x != self.last_hover_grid_x or 
                        grid_y != self.last_hover_grid_y):
                        hover_sound_should_play = True
                        self.currently_hovering_grid = True
                        self.last_hover_grid_x = grid_x
                        self.last_hover_grid_y = grid_y
                else:
                    self.currently_hovering_grid = False
                    self.last_hover_grid_x = None
                    self.last_hover_grid_y = None

        if hover_sound_should_play:
            hover_sound.play()

        # Draw score animation
        if self.score_animation:
            current_time = pygame.time.get_ticks()
            if current_time - self.score_animation_time < 700:
                score_font = pygame.font.SysFont(None, 48)
                animation_text = score_font.render(
                    f'+{self.score_animation["score"]} (×{self.score_animation["multiplier"]})',
                    True, GREEN
                )
                text_rect = animation_text.get_rect(center=(WINDOW_WIDTH//2, self.score_animation['y']))
                SCREEN.blit(animation_text, text_rect)
                self.score_animation['y'] -= 2
            else:
                self.score_animation = None

        # Game over overlay
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
                    shape_start_y = SCORE_AREA_HEIGHT + GRID_PIXELS + 50
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
                            grid_y = (mouse_y - shape.offset_y - SCORE_AREA_HEIGHT) // (CELL_SIZE + MARGIN)

                            if game.can_place_shape(shape, grid_x, grid_y):
                                game.place_shape(shape, grid_x, grid_y)
                            shape.dragging = False

        game.draw()
        clock.tick(60)

    pygame.quit()
    await asyncio.sleep(0)

if __name__ == '__main__':
    asyncio.run(main())
