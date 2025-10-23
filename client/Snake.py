from socket import socket
from tkinter import ALL
import tkinter as tk
import random
from typing import ParamSpecArgs
import networking as n
from host import Host, Client
import socket
import threading

# from pygame import mixer
x, y =15,15
direction = ''
posicion_x = 15
posicion_y = 15
posicion_food = (15,15)
posicion_snake = [(75,75)]
nueva_posicion =[(15,15)]
last_dir = 'left'
# mixer.init()


    
class SnakeGameFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.config(bg='black')
        self.master.resizable(0, 0)

        if self.master.host:
            print("Starting host server ")
            self.host = Host(self.master.num_players)
            self.host.start()

        self.create_widgets()
        self.master.update_idletasks()
        self.master.geometry('485x510')
        self.bind_events()

        self.id = None
        self.alive = True

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.master.host_ip, int(self.master.host_port)))


        CLIENT_TRHEAD = threading.Thread(target=self.listen_host, daemon=True).start()

        
    def listen_host(self):
        while True:
            try:
                msg = n.recv_pickle(self.client_socket)
                # print(f"Received: {msg}")
                if msg['type'] == 'new_player_ack':
                    self.after(0, lambda msg=msg: self.new_me(msg))
                elif msg['type'] == 'new_player':
                    self.after(0, lambda msg=msg: self.new_player(msg))
                elif msg['type'] == 'main_loop_food':
                    self.after(0, lambda msg=msg: self.update_food(msg))
                elif msg['type'] == 'main_loop_client':
                    self.after(0, lambda msg=msg: self.update_snake(msg))
                elif msg['type'] == 'start_game':
                    self.after(0, lambda msg=msg: self.movimiento())
            except Exception as e:
                print(f"Error idk wtf, error {e}")
                break



    def new_me(self, msg):
        global x,y, direction
        self.id = msg['id']
        player = msg['info']
        self.color = player.color
        self.create_snake(player)
        x, y = player.position[0]
        direction = 'right'
        print(f"snake pos {player.position}")

        self.snake_color= tk.Label(self.frame_1, text='Snake ■ :', bg='black',
                                 fg=player.color, font=('Arial', 12, 'bold'))
        self.snake_color.grid(row=0, column=2, padx=20)

    def new_player(self, msg):
        player : Client = msg['info']
        self.create_snake(player)

    def create_snake(self, player : Client):
        id = str(player.id)
        self.canvas.create_rectangle(player.position[0][0], player.position[0][1], player.position[0][0]+30, player.position[0][1]+30, fill=player.color,outline='black' , tag =id)
        self.canvas.update_idletasks()
        
    def find_obj_by_tag(self, tag):
        return [obj for obj in self.canvas.find_all() if tag in self.canvas.gettags(obj)] 

    def update_snake(self, msg):
        player = msg['info']
        if player.id == self.id:
            self.alive = player.alive
        id = str(player.id)
        obj = self.find_obj_by_tag(id)

        if not player.alive:
            for o in obj:
                self.canvas.delete(o)
            return

        if msg['respawn']:
            self.canvas.create_rectangle(player.position[0][0], player.position[0][1], player.position[0][0]+30, player.position[0][1]+30, fill=player.color,outline='black' , tag =id)

        for parte, lugar in zip(obj, player.position):
            lugar = list(lugar)
            lugar.append(lugar[0]+30)
            lugar.append(lugar[1]+30)
            lugar = tuple(lugar)
            # print(f"parte: {parte}, lugar: {lugar}")
            self.canvas.coords(parte, *lugar)
        if msg['ate']:
            self.canvas.create_rectangle(player.position[0][0], player.position[0][1], player.position[0][0]+30, player.position[0][1]+30, fill=player.color,outline='black' , tag =id)

    def update_food(self, msg):
        coord = msg['info']
        self.canvas.coords(self.canvas.find_withtag("food"),coord)

    def create_widgets(self):
        # Frame superior
        self.frame_1 = tk.Frame(self.master, bg='black') # , width=485, height=25
        self.frame_1.pack()

        # Frame inferior
        self.frame_2 = tk.Frame(self.master, bg='black') # , width=485, height=490
        self.frame_2.pack(fill = 'both', expand = True)

        # Canvas
        self.canvas = tk.Canvas(self.frame_2, bg='black' , width=479, height=479) 
        self.canvas.pack(expand = True)

        # Dibujar la cuadrícula
        for i in range(0, 460, 30):
            for j in range(0, 460, 30):
                self.canvas.create_rectangle(i, j, i+30, j+30, fill='gray10')

        self.canvas.create_text(75, 75, text='🍎', fill='red2',
                                font=('Arial', 18), tag='food')

        # Botones y etiquetas
        self.button1 = tk.Button(self.frame_1, text='Salir', bg='orange', command=self.salir)
        self.button1.grid(row=0, column=0, padx=20)

        self.button2 = tk.Button(self.frame_1, text='Respawn', bg='aqua', command=self.respawn)
        self.button2.grid(row=0, column=1, padx=20)

        # self.snake_color= tk.Label(self.frame_1, text='Snake ■ :', bg='black',
        #                          fg='white', font=('Arial', 12, 'bold'))
        # self.snake_color.grid(row=0, column=2, padx=20)

    def bind_events(self):
        self.master.bind("<KeyPress-Up>", lambda event: self.direccion('up'))
        self.master.bind("<KeyPress-Down>", lambda event: self.direccion('down'))
        self.master.bind("<KeyPress-Left>", lambda event: self.direccion('left'))
        self.master.bind("<KeyPress-Right>", lambda event: self.direccion('right'))

    def coordenadas_snake(self):
        global direccion, posicion_snake,x,y ,nueva_posicion 
        if direction =='up': # arriba
            y =  y-30
            nueva_posicion[0:] = [(x, y)]
            if y >=480:
                y=-30
            elif y <0:
                y=480
        elif direction =='down':  # abajo
            y = y+30 
            nueva_posicion[0:] = [(x, y)]
            if y >=480:
                y=-30
            elif y <0:
                y=-30    
        elif direction == 'left': # izquierda
            x = x-30
            nueva_posicion[0:] = [(x, y)]
            if x >=480:
                x = -30
            elif x <0:
                x=480
        elif direction == 'right':  # derecha
            x = x + 30
            nueva_posicion[0:] = [(x, y)]
            if x >=480:
                x=-30
            elif x <0:
                x=-30
        global last_dir 
        last_dir = direction
        msg = {
            'type': 'move',
            'info': nueva_posicion[0]
        }
        n.send_pickle(self.client_socket, msg)
        

    def direccion(self,event):
        global direction, last_dir
        if event == 'left':
            if last_dir!= 'right':
                direction = event
        elif event == 'right':
            if last_dir!= 'left':
                direction = event
        elif event == 'up':
            if last_dir!= 'down':
                direction = event
        elif event == 'down':
            if last_dir!= 'up':
                direction = event

   

    def movimiento(self):
        global posicion_food, posicion_snake,nueva_posicion
         
        if self.alive:
            self.coordenadas_snake()

        self.after(150, self.movimiento)


    def respawn(self):
        print(f'Trying respawn {self.alive}')
        if self.alive:
            return
        msg = {
            'type': 'respawn',
        }
        print(f"Sening respawn")
        n.send_pickle(self.client_socket, msg)



    def salir (self):
        self.client_socket.close()
        self.after(0,self.destroy)
        self.after(0, self.quit)

# Crear ventana principal y ejecutar
if __name__ == "__main__":
    root = tk.Tk()
    app = SnakeGameFrame(master=root)
    app.mainloop()







