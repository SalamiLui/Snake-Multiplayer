import networking as n
import socket
import threading
import random


class Client:
    def __init__(self, client_socket):
        self.id = client_socket.fileno()
        self.position = list()
        self.alive = True
        self.color = None



class Host:
    def __init__(self, nplayers):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", 5569))
        self.server.listen()
        self.clients = dict()
        self.free_spaces = set((x, y) for x in range(0,451,30) for y in range(0,451,30))        
        self.food = [] 
        self.lock = threading.Lock()
        self.num_players = nplayers

        self.start_positions = [((0,0),'green2'), ((0,450),'blue'), ((450,0),'red'), ((450,450),'yellow')]

    def start(self):
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self):
        while True:
            client, addr = self.server.accept()
            print(f"Conectado: {addr}")
            self.new_client(client)
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        while True:
            try:
                msg = n.recv_pickle(client)
                # print(f"Received: {msg}")
                if msg['type'] == 'move':
                    self.handle_move(client, msg)
                elif msg['type'] == 'respawn':
                    self.handle_respawn(client, msg)
                elif msg['type'] == 'respawn':
                    print("handling Respawn")
                    self.handle_respawn(client, msg)

            except Exception as e:
                print(f"Error: Client Disconnected, error {e}")
                self.close_client(client)
                break

    def handle_respawn(self, client, msg):
        pos = self.pick_rand_pos()
        if pos == None:
            return #handle error 
        self.clients[client].position.append(pos)
        self.free_spaces.discard(pos)
        self.clients[client].alive = True
        self.update_clients(client, respawn = True)


    def handle_move(self, client, msg):
        head = msg['info']
        alive, ate = self.track_collisions(head)
        self.clients[client].alive = alive
        self.update_position(client, head, ate, alive)        
        if ate:
            self.spawn_food()

    def update_position(self, client, head, ate, alive):
        snake_body = self.clients[client].position
        if not alive:
            for coord in snake_body:
                if not (coord[0] < 0 or coord[0] > 450 or coord[1] < 0 or coord[1] > 450):
                    self.free_spaces.add(coord)
            snake_body.clear()
            self.update_clients(client)
            return
        snake_body.insert(0, head)
        if not (head [0] < 0 or head[0] > 450 or head[1] < 0 or head[1] > 450):
            self.free_spaces.discard(head)
        if not ate:
            tail = snake_body.pop()
            if not (tail[0] < 0 or tail[0] > 450 or tail[1] < 0 or tail[1] > 450):
                self.free_spaces.add(tail)
        self.update_clients(client, ate)
        # print(f"snake body {snake_body}")


    def track_collisions(self, head):
        alive, ate = True, False
        for c in self.clients:
            if head in self.clients[c].position:
                alive = False
        cphead = list(head)
        cphead[0] = cphead[0] + 15
        cphead[1] = cphead[1] + 15
        cphead = tuple(cphead)
        if cphead == self.food:
            ate = True
        return alive, ate

    def pick_rand_pos(self):
        if len(self.free_spaces) == 0:
            return None
        return random.choice(list(self.free_spaces))

    def spawn_food(self):
        self.food = self.pick_rand_pos()
        self.food = list(self.food)
        self.food[0] = self.food[0] + 15
        self.food[1] = self.food[1] + 15
        self.food = tuple(self.food)
        print(f"food {self.food}")
        if self.food == None:
            return #handle error
        self.free_spaces.discard(self.food)
        self.update_food()

    def new_client(self, client):
        rand_pos, color = self.start_positions.pop(random.randint(0, len(self.start_positions) - 1))
        with self.lock:
            self.clients[client] = Client(client)
        self.clients[client].position.append(rand_pos)
        self.clients[client].color = color
        # self.clients[client].position.append(rand_pos)
        self.free_spaces.discard(rand_pos)

        msg = {
            'type': 'new_player_ack',
            'id' : client.fileno(),
            'info' : self.clients[client]
        }
        n.send_pickle(client, msg)

        for c in self.clients:
            if c != client:
                msg = {
                    'type': 'new_player',
                    'id' : c.fileno(),
                    'info' : self.clients[c]
                }
                n.send_pickle(client, msg)

        msg = {
            'type': 'new_player',
            'id' : client.fileno(),
            'info' : self.clients[client]
        }
        for c in self.clients:
            if c != client:
                n.send_pickle(c, msg)
        if len(self.clients) == self.num_players:
            self.spawn_food()
            msg = {
                'type': 'start_game',
            }
            for c in self.clients:
                n.send_pickle(c, msg)


    def update_clients(self, client, ate = False, respawn = False):
        msg = {
            'type': 'main_loop_client',
            'info' : self.clients[client],
            'ate' : ate,
            'respawn' : respawn
        }
        for c in self.clients:
            try:
                n.send_pickle(c, msg)
            except:
                pass

    def update_food(self):
        msg = {
            'type': 'main_loop_food',
            'info' : self.food

        }
        for c in self.clients:
            n.send_pickle(c, msg)
            

    def close_client(self, client):
        self.clients[client].alive = False
        for coord in self.clients[client].position:
            self.free_spaces.add(coord)
        self.clients[client].position.clear()
        self.update_clients(client)
        with self.lock:
            self.clients.pop(client)
        client.close()

