import socket
import json
import pygame

# Initialize Pygame
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Multiplayer Light Bike Game')

# Connect to Server
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('127.0.0.1', 25565))  # Replace 'localhost' with the server's IP if not running locally

# Set the socket to non-blocking
client_socket.setblocking(0)

# Print connection status in the terminal
print("Connected to Server")

# Display connection status on the screen
myfont = pygame.font.SysFont('Comic Sans MS', 30)
text_surface = myfont.render('Connected to Server', False, (0, 255, 0))
screen.blit(text_surface, (350, 10))
pygame.display.update()

def send_to_server(data):
    serialized_data = json.dumps(data)
    client_socket.send(serialized_data.encode('utf-8'))
    print("Sent data to server")  # Debugging print

def receive_from_server():
    try:
        data = client_socket.recv(4096).decode('utf-8')
        return json.loads(data)
    except:
        print("No data received from server or error occurred")  # Debugging print
        return None

# Function to draw a player
def draw_player(x, y, color):
    pygame.draw.rect(screen, color, (x, y, 10, 10))

# Function to draw trails
def draw_trail(trail, color):
    for point in trail:
        pygame.draw.rect(screen, color, (point['x'], point['y'], 10, 10))

# Main game loop
try:
    while True:
        pygame.time.delay(100)  # Delay to prevent high CPU usage
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            print("Left key pressed")  # Debugging print
            send_to_server({'action': 'move', 'direction': 'left'})
        elif keys[pygame.K_RIGHT]:
            print("Right key pressed")  # Debugging print
            send_to_server({'action': 'move', 'direction': 'right'})
        elif keys[pygame.K_UP]:
            print("Up key pressed")  # Debugging print
            send_to_server({'action': 'move', 'direction': 'up'})
        elif keys[pygame.K_DOWN]:
            print("Down key pressed")  # Debugging print
            send_to_server({'action': 'move', 'direction': 'down'})

        latest_game_state = receive_from_server()
        if latest_game_state:
            print("Latest game state:", latest_game_state)
            screen.fill((0, 0, 0))
            for addr, player_data in latest_game_state['players'].items():
                print(f"Drawing player at ({player_data['x']}, {player_data['y']}) with color {player_data['color']}")
                draw_player(player_data['x'], player_data['y'], player_data['color'])
                draw_trail(player_data['trail'], player_data['color'])

            screen.blit(text_surface, (350, 10))
            pygame.display.update()
            print("Screen updated")  # Additional debugging
        else:
            print("No game state received, skipping drawing.")  # Additional debugging
except Exception as e:
    print(f"An error occurred: {e}")