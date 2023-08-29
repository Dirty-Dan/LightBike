import pygame
import sys
import math
import time
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.Info().current_w, pygame.display.Info().current_h
BIKE_SIZE = 20
BIKE_LENGTH = 50
TRAIL_FADE_TIME = 10  # Time in seconds for trail to fade

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
CYAN_BLUE = (0, 255, 255)
MAGENTA = (255, 0, 255)

# Create screen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption('Multiplayer Light Bike Game')

def start_screen():
    font = pygame.font.Font(None, 74)
    text = font.render("Enter Number of Bots: ", True, (255, 0, 0))
    input_box = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, 140, 32)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text_input = ''
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        return int(text_input)  # Convert to integer
                    elif event.key == pygame.K_BACKSPACE:
                        text_input = text_input[:-1]
                    else:
                        text_input += event.unicode

        screen.fill((0, 0, 0))
        txt_surface = font.render(text_input, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        screen.blit(text, (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - 50))
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)
        
        pygame.display.flip()
        clock.tick(30)

class Player:
    def __init__(self, x, y, angle, color, trail_color, controls):
        self.x = x
        self.y = y
        self.angle = angle
        self.color = color
        self.trail_color = trail_color
        self.trail_points = []
        self.controls = controls
        self.next_change_time = 0  # When to change direction next
        self.move_direction = None  # What direction to move in
        self.min_distance = 50  # (For Bot Logic, Minimum distance to move in one direction
        self.distance_moved = 0  # (For Bot Logic, Distance moved in the current direction

    def move(self, keys):
        if keys[self.controls.get('up', 0)]:
            self.y -= 5
            self.angle = 90
        if keys[self.controls.get('down', 0)]:
            self.y += 5
            self.angle = 270
        if keys[self.controls.get('left', 0)]:
            self.x -= 5
            self.angle = 180
        if keys[self.controls.get('right', 0)]:
            self.x += 5
            self.angle = 0

    def draw(self):
        wheel1_x = self.x + (BIKE_LENGTH / 2) * math.cos(math.radians(self.angle))
        wheel1_y = self.y + (BIKE_LENGTH / 2) * math.sin(math.radians(self.angle))
        wheel2_x = self.x - (BIKE_LENGTH / 2) * math.cos(math.radians(self.angle))
        wheel2_y = self.y - (BIKE_LENGTH / 2) * math.sin(math.radians(self.angle))
        
        pygame.draw.circle(screen, self.color, (int(wheel1_x), int(wheel1_y)), BIKE_SIZE // 2)
        pygame.draw.circle(screen, self.color, (int(wheel2_x), int(wheel2_y)), BIKE_SIZE // 2)
        
        pygame.draw.line(screen, self.color, (wheel1_x, wheel1_y), (wheel2_x, wheel2_y), 5)

    def check_collision(self, other_trail):
        for t, x, y in other_trail:
            if math.sqrt((self.x - x)**2 + (self.y - y)**2) < BIKE_SIZE:
                return True
        return False
    
    def smart_move(self, target_x, target_y, all_trails):
        directions = ['up', 'down', 'left', 'right']

        # If distance moved is less than minimum, keep moving in the same direction
        if self.distance_moved < self.min_distance:
            self.distance_moved += 5
            return
        # Reset the distance moved
        self.distance_moved = 0
    
    # Remove directions that lead to a collision
        safe_directions = []
        for direction in directions:
            new_x, new_y = self.x, self.y
        
            if direction == 'up':
                new_y -= 5
            elif direction == 'down':
                new_y += 5
            elif direction == 'left':
                new_x -= 5
            elif direction == 'right':
                new_x += 5
        
            collision = False
            for trail in all_trails:
                if self.will_collide(new_x, new_y, trail):
                    collision = True
                    break
        
            if not collision:
                safe_directions.append(direction)
            
        if safe_directions:
            self.move_direction = random.choice(safe_directions)
        else:
            self.move_direction = random.choice(directions)

    def will_collide(self, x, y, other_trail):
        for t, trail_x, trail_y in other_trail:
            if math.sqrt((x - trail_x)**2 + (y - trail_y)**2) < BIKE_SIZE:
                return True
        return False


        
        # Randomly mix in the current direction to make it less predictable
        if self.move_direction:
            directions += [self.move_direction] * 2

        self.move_direction = random.choice(directions)


# Initialize human player
player1 = Player(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2, 0, BLUE, CYAN_BLUE, {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d})

# Start screen to ask for number of bots
num_bots = start_screen()

# Initialize bots
bots = [Player((i + 1) * SCREEN_WIDTH // (num_bots + 1), SCREEN_HEIGHT // 2, 0, RED, MAGENTA, {}) for i in range(num_bots)]

players = [player1] + bots

# Main game loop
clock = pygame.time.Clock()
while True:
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    # Fill screen with black
    screen.fill(BLACK)

    # Update and draw players
    for player in players:
        player.trail_points = [(t, x, y) for t, x, y in player.trail_points if current_time - t <= TRAIL_FADE_TIME]

        if player in bots:  # Bot logic (random movement)
            all_trails = [other_player.trail_points for other_player in players if other_player != player]
            player.smart_move(player1.x, player1.y, all_trails)
                

            new_x, new_y = player.x, player.y  # Temporary variables to hold the new positions

            if player.move_direction == 'up':
                new_y -= 5
            elif player.move_direction == 'down':
                new_y += 5
            elif player.move_direction == 'left':
                new_x -= 5
            elif player.move_direction == 'right':
                new_x += 5

        # Boundary check
            if 0 <= new_x <= SCREEN_WIDTH and 0 <= new_y <= SCREEN_HEIGHT:
                player.x, player.y = new_x, new_y  # Update positions only if within the boundary
            else:
                player.next_change_time = 0  # Force the bot to choose a new direction

        else:  # Human player
            player.move(keys)

        # Add current position to trail points with timestamp
        player.trail_points.append((current_time, player.x, player.y))

        # Draw player
        player.draw()

    # ... (rest of the code remains the same)


    # Check for collisions
    for player in players:
        for other_player in players:
            if player != other_player and player.check_collision(other_player.trail_points):
                if player == player1:
                    print("Game Over")
                    pygame.quit()
                    sys.exit()
                elif other_player == player1:
                    players.remove(player)

    if len(players) == 1 and player1 in players:
        print("You won")
        pygame.quit()
        sys.exit()

    # Draw the trails
    for player in players:
        for i in range(1, len(player.trail_points)):
            pygame.draw.line(screen, player.trail_color, (player.trail_points[i-1][1], player.trail_points[i-1][2]), (player.trail_points[i][1], player.trail_points[i][2]), 5)

    # Update screen
    pygame.display.update()
    clock.tick(60)
