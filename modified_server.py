import socket
import select
import json

# Initialize the game state
game_state = {'players': {}}

# Initialize a Server Socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 25565))
server_socket.listen(10)

connection_list = [server_socket]
print("Server started on 0.0.0.0:25565")

def broadcast_game_state():
    serialized_state = json.dumps(game_state)
    for client_socket in connection_list:
        if client_socket != server_socket:
            client_socket.send(serialized_state.encode('utf-8'))
            print(f"Sent game state to client: {client_socket.getpeername()}")  # Debugging print

while True:
    read_sockets, _, _ = select.select(connection_list, [], [])
    
    for sock in read_sockets:
        if sock == server_socket:
            client_socket, addr = server_socket.accept()
            connection_list.append(client_socket)
            print(f"Client ({addr}) connected")

            # Assign initial state for the new player
            game_state['players'][str(addr)] = {'x': 0, 'y': 0, 'color': [255, 0, 0], 'trail': []}
            
            broadcast_game_state()
            
        else:
            addr = str(sock.getpeername())  # Get the address of the connected client
            try:
                data = sock.recv(4096).decode('utf-8')
                if data:
                    print(f"Receiving data from {addr}...")  # Debugging print
                    received_data = json.loads(data)
                    
                    # Update the game state based on received data
                    if received_data['action'] == 'move':
                        direction = received_data['direction']
                        if direction == 'left':
                            game_state['players'][addr]['x'] -= 1
                        elif direction == 'right':
                            game_state['players'][addr]['x'] += 1
                        elif direction == 'up':
                            game_state['players'][addr]['y'] -= 1
                        elif direction == 'down':
                            game_state['players'][addr]['y'] += 1
                            
                    # Update the player's trail
                    new_trail_point = {'x': game_state['players'][addr]['x'], 'y': game_state['players'][addr]['y']}
                    game_state['players'][addr]['trail'].append(new_trail_point)
                    
                    # Debugging: Print the updated game state
                    print("Updated game state:", game_state)
                    
                    broadcast_game_state()
                    
            except Exception as e:
                print(f"Client ({addr}) is offline or an error occurred: {e}. Removing client from list.")  # Debugging print
                sock.close()
                connection_list.remove(sock)
                del game_state['players'][addr]  # Remove the player from the game state
                continue
