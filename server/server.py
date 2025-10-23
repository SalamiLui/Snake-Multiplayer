import socket
import threading
import serverDB as db 
from rooms import Room
import networking as n 

BUFFER_SIZE = 4096



class GameServer:
    def __init__(self, host_ip, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host_ip, port))
        self.server.listen()
        self.clients = [] 
        self.names = set()
        self.lock = threading.Lock()
        self.running = True
        self.rooms = [Room() for _ in range(4)]
        print(f"Esperando jugadores en {host_ip}:{port}")

    def accept_clients(self):
        while self.running: 
            client, addr = self.server.accept()
            print(f"Conectado: {addr}")
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client):
        while True:
            try:
                msg = n.recv_pickle(client)

                print(f"Received: {msg}")   

                if msg['type'] == 'login':
                    self.login_client(client, msg)  
                elif msg['type'] == 'signup':
                    self.signup_client(client, msg)
                elif msg['type'] == 'msg':
                    self.msg_client(client, msg)
                elif msg['type'] == 'join_room':
                    self.join_room(client, msg)
                elif msg['type'] == 'leave_room':
                    self.leave_room(client, msg)
                elif msg['type'] == 'start_room':
                    self.start_room(client, msg)
                
            except Exception as e:
                print(f"Error: Client Disconnected, error {e}")
                self.close_client(client)
                break

    def login_client(self, client, msg):
        if msg['username'] in self.names:
            response = {'type': 'login_ack', 'ok': False, 'error': 'Already logged in'}
            n.send_pickle(client, response)
            return

        login_status = db.login(msg['username'], msg['password'])
        if login_status == db.Status.SUCCESS:
            print(f"Logged in: {msg['username']}")
            response = {'type': 'login_ack', 'ok': True}
            n.send_pickle(client, response)
            with self.lock:
                self.names.add(msg['username'])
                self.clients.append((client, msg['username']))  
            _ = n.recv_pickle(client)
            self.update_on_start(client)
        elif login_status == db.Status.INVALID_NAME:
            response = {'type': 'login_ack', 'ok': False, 'error': 'Invalid name'}
            n.send_pickle(client, response)
        elif login_status == db.Status.INVALID_PASSWORD:
            response = {'type': 'login_ack', 'ok': False, 'error': 'Invalid password'}
            n.send_pickle(client, response)
        else:
            response = {'type': 'login_ack', 'ok': False, 'error': 'Unknown error'}
            n.send_pickle(client, response)


    def signup_client(self, client, msg):
        if msg['username'] in self.names:
            response = {'type': 'signup_ack', 'ok': False, 'error': 'Already logged in'}
            n.send_pickle(client, response)
            return

        signup_status = db.signup(msg['username'], msg['password'])
        if signup_status == db.Status.SUCCESS:
            print(f"Signed up: {msg['username']}")
            response = {'type': 'signup_ack', 'ok': True}
            n.send_pickle(client, response)
            with self.lock:
                self.names.add(msg['username'])
                self.clients.append((client, msg['username'])) 
            _ = n.recv_pickle(client)
            self.update_on_start(client)
        elif signup_status == db.Status.INVALID_NAME:
            response = {'type': 'signup_ack', 'ok': False, 'error': 'Invalid name'}
            n.send_pickle(client, response)
        else:
            response = {'type': 'signup_ack', 'ok': False, 'error': 'Unknown error'}
            n.send_pickle(client, response)


    def update_on_start(self, client):
        self.update_online_list()
        for iRoom in range(4):
            msg = {
            'type': 'room_list',
            'room': iRoom,
            'clients': self.rooms[iRoom].clients,
            'host': self.rooms[iRoom].host
            }
            try:
                n.send_pickle(client, msg)
            except Exception as e:
                print(f"Skill issue: {e}")
                print(f"msg: {msg}")



    def update_online_list(self):
        name_list = list(self.names)
        for client, _ in self.clients:
            try:
                response = {'type': 'online_list', 'names': name_list}
                n.send_pickle(client, response)
            except:
                pass

    def update_room_list(self, iRoom : int):
        msg = {
            'type': 'room_list',
            'room': iRoom,
            'clients': self.rooms[iRoom].clients,
            'host': self.rooms[iRoom].host
        }

        for client, _ in self.clients:
            try:
                n.send_pickle(client, msg)
            except Exception as e:
                print(f"Skill issue: {e}")
                print(f"msg: {msg}")


    def msg_client(self, client, msg):

        for c, _ in self.clients:
            try:
                if c != client:
                    n.send_pickle(c, msg)
            except:
                pass

        
    def close_client(self, client):
        name = ""
        for i, (c,n) in enumerate(self.clients):
            if c == client:
                name = n
                with self.lock:
                    self.names.remove(n)
                    self.clients.pop(i)
                break

        for i, room in enumerate(self.rooms):
            for c in room.clients:
                if c == name:
                    with self.lock:
                        room.remove_client(name)
                    self.update_room_list(i)
                    break

        client.close()
        self.update_online_list()


    def join_room(self, client, msg):
        print(f"Client joining room: {msg['room']}")
        with self.lock:
            room = self.rooms[msg['room']]
            ok = room.add_client(msg['name'])
        if ok:
            response = {'type': 'join_room_ack', 'ok': True, 'room': msg['room']}
            n.send_pickle(client, response)
            print("Updating room list")
            self.update_room_list(msg['room'])
        else:
            response = {'type': 'join_room_ack', 'ok': False, 'error': 'Room is full'}
            n.send_pickle(client, response)

    def leave_room(self,_, msg):
        with self.lock:
            room = self.rooms[msg['room']]
            room.remove_client(msg['name'])
        self.update_room_list(msg['room'])

    def start_room(self,client,  msg):
        room = self.rooms[msg['room']]
        ip, port = "", "5569"
        for c, name in self.clients:
            if name == room.host:
                ip, _ = c.getsockname()
                break
        response = {
            'type': 'start_game',
            'ip': ip,
            'port': port,
            'num_players': len(room.clients)
        }
        rclients = room.clients.copy()
        for c, name in self.clients:
            if name in rclients and c != client:
                n.send_pickle(c, response)
                self.close_client(c)
        n.send_pickle(client, response)
        self.close_client(client)
         
        


def start_server( host_ip='0.0.0.0', port=5555):
    server = GameServer(host_ip, port)
    server.accept_clients()  
    return server

start_server('127.0.0.1', 5555)
