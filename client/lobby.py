import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading 
import networking as n
import Snake


NEON_COLOR = "#39ff14"
BG_COLOR = "#0f0f0f"
FONT = ("Courier New", 11, "bold")
CHAT_COLOR = "#ff00ff"
PLAYER_COLOR = "#00ffff"
SALA_COLORS = ["#39ff14", "#00ccff", "#ff00ff", "#ff9900"]




class App(tk.Tk):
    def __init__(self, start_frame):
        super().__init__()
        self.title("Snake 3.0")
        self.geometry("1000x600")
        
        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True)

        self.client_socket = None  # Aquí se guardará el socket
        self.current_frame = None
        self.client_name = "Sadam Hussein"

        self.show_frame(start_frame)

        self.host : bool = False
        self.host_ip : str = None
        self.host_port : int = 5569
        self.num_players : int = None


    def show_frame(self, frame_class):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = frame_class(self)
        self.current_frame.pack(expand=True, fill="both")
    

class ConnectFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_COLOR)
        self.master = master
        self.client_socket = master.client_socket
        self.show_frame = master.show_frame

        tk.Label(self, text="Conectar al servidor", fg=NEON_COLOR, bg=BG_COLOR, font=FONT).pack(pady=10)

        self.entry_ip = tk.Entry(self, fg=NEON_COLOR, bg="#1a1a1a", insertbackground=NEON_COLOR,
                                 highlightthickness=1, highlightbackground=NEON_COLOR, font=FONT, relief="flat")
        self.entry_ip.insert(0, "127.0.0.1")
        self.entry_ip.pack(pady=5, ipadx=10, ipady=5)

        self.entry_port = tk.Entry(self, fg=NEON_COLOR, bg="#1a1a1a", insertbackground=NEON_COLOR,
                                   highlightthickness=1, highlightbackground=NEON_COLOR, font=FONT, relief="flat")
        self.entry_port.insert(0, "5555")
        self.entry_port.pack(pady=5, ipadx=10, ipady=5)

        tk.Button(self, text="Conectar", command=self.connect_to_server,
                  fg=BG_COLOR, bg=NEON_COLOR, activebackground="#00cc00",
                  font=FONT, relief="flat").pack(pady=10, ipadx=10, ipady=5)

    def connect_to_server(self):
        ip = self.entry_ip.get()
        port = int(self.entry_port.get())
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            self.master.client_socket = sock  # Guardamos el socket en la app principal
            self.show_frame(LoginFrame)  # Cambiar a la siguiente ventana
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))

class LoginFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_COLOR)
        self.master = master
        self.client_socket = master.client_socket
        self.show_frame = master.show_frame
    

        tk.Label(self, text="Login", fg=NEON_COLOR, bg=BG_COLOR, font=FONT).pack(pady=10)

        self.username = tk.Entry(self, fg=NEON_COLOR, bg="#1a1a1a", insertbackground=NEON_COLOR,
                                 highlightthickness=1, highlightbackground=NEON_COLOR, font=FONT, relief="flat")
        self.username.pack(pady=5, ipadx=10, ipady=5)

        self.password = tk.Entry(self, show="*", fg=NEON_COLOR, bg="#1a1a1a", insertbackground=NEON_COLOR,
                                 highlightthickness=1, highlightbackground=NEON_COLOR, font=FONT, relief="flat")
        self.password.pack(pady=5, ipadx=10, ipady=5)

        tk.Button(self, text="Iniciar sesión", command=self.login,
                  fg=BG_COLOR, bg=NEON_COLOR, activebackground="#00cc00",
                  font=FONT, relief="flat").pack(pady=10, ipadx=10, ipady=5)

    def login(self):
        msg = {
            'type': 'login',
            'username': self.username.get(),
            'password': self.password.get()
        }
        try:
            n.send_pickle(self.client_socket, msg)
            response= n.recv_pickle(self.client_socket)
            if response['ok']:
                self.master.client_name = self.username.get()
                self.show_frame(LobbyFrame)
            elif response['error'] == 'Invalid name': 
                ans = messagebox.askyesno("Confirmación", "Nombre de usuario no existe, desa crearlo?")
                if ans:
                    self.signup() 
            elif response['error'] == 'Invalid password':
                messagebox.showerror("Error", "Contraseña incorrecta")
            else:
                messagebox.showerror("Error", response['error'])

        except:
            pass

    def signup(self):
        msg2 ={
            'type': 'signup',
            'username': self.username.get(),
            'password': self.password.get()
        }
        n.send_pickle(self.client_socket, msg2)
        response= n.recv_pickle(self.client_socket)
        if response['ok']:
            self.master.client_name = self.username.get()
            self.show_frame(LobbyFrame)
        else:
            messagebox.showerror("Error", response['error'])

            
class LobbyFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG_COLOR)
        self.master = master
        self.client_socket = master.client_socket
        self.client_name = master.client_name
        self.rooms_listbox = []
        self.current_room = None
        self.isHost = False
        self.show_frame = master.show_frame

        self.master.update_idletasks()
        self.master.geometry('1500x1000')

        self.username_label = tk.Label(
            self,
            text=f"Jugador: {self.client_name}",              font=("Courier New", 20, "bold"),
            bg=BG_COLOR,
            fg=CHAT_COLOR,
        )

        self.username_label.pack(side="top", pady=(20, 10))

# Simulando un pequeño glow al pasar el mouse
        self.username_label.bind("<Enter>", lambda e: self.username_label.config(fg="#ffffff"))
        self.username_label.bind("<Leave>", lambda e: self.username_label.config(fg=CHAT_COLOR))


        # =============== LEFT: Jugadores Online ===================
        self.left_frame = tk.Frame(self, bg=BG_COLOR)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(self.left_frame, text="Jugadores Online", fg=PLAYER_COLOR,
                 bg=BG_COLOR, font=FONT).pack(anchor="nw")

        self.players_listbox = tk.Listbox(self.left_frame, bg="#1a1a1a", fg=PLAYER_COLOR,
                                          selectbackground="#333", font=FONT, height=20,
                                          highlightthickness=1, highlightbackground=PLAYER_COLOR,
                                          relief="flat")
        self.players_listbox.pack(pady=5, fill="y", expand=True)

        # =============== CENTER: Salas ===================
        self.center_frame = tk.Frame(self, bg=BG_COLOR)
        self.center_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        tk.Label(self.center_frame, text="Salas", fg="#ffffff", bg=BG_COLOR, font=FONT).pack()

        for i in range(4):
            sala_frame = tk.Frame(self.center_frame, bg="#1a1a1a", bd=2,
                                  highlightbackground=SALA_COLORS[i],
                                  highlightthickness=2)
            sala_frame.pack(pady=10, fill="x", padx=20)

            tk.Label(sala_frame, text=f"Sala {i+1}", fg=SALA_COLORS[i],
                     bg="#1a1a1a", font=FONT).pack(anchor="w", padx=5, pady=2)

            players = tk.Listbox(sala_frame, height=4, bg="#262626", fg=SALA_COLORS[i],
                                 highlightthickness=0, font=FONT, relief="flat")
            players.pack(fill="x", padx=5)

            btn = tk.Button(sala_frame, text="Unirse / Salir", font=FONT,
                            bg=SALA_COLORS[i], fg=BG_COLOR,
                            activebackground="#000000", activeforeground=SALA_COLORS[i],
                            relief="flat", cursor="hand2", command=lambda sala=i: self.toggle_room(sala))
            btn.pack(pady=5, padx=5, ipadx=5, ipady=2)


            self.rooms_listbox.append(players)


    # =============== Botón Ocultable ===================
        self.bottom_center_frame = tk.Frame(self.center_frame, bg=BG_COLOR)
        self.bottom_center_frame.pack(pady=10)

        self.start_room = tk.Button(
            self.bottom_center_frame,
            text="Iniciar Partida",
            font=("Courier New", 14, "bold"),
            bg=CHAT_COLOR,
            fg=BG_COLOR,
            activebackground="#000000",
            activeforeground=CHAT_COLOR,
            relief="flat",
            cursor="hand2",
            command=self.start_room_action
        )
        # self.start_room.pack(pady=(20, 10), ipadx=10, ipady=5)

# Efecto glow
        self.start_room.bind("<Enter>", lambda e: self.start_room.config(bg="#ffffff", fg=CHAT_COLOR))
        self.start_room.bind("<Leave>", lambda e: self.start_room.config(bg=CHAT_COLOR, fg=BG_COLOR))


        # =============== RIGHT: Chat ===================
        self.right_frame = tk.Frame(self, bg=BG_COLOR)
        self.right_frame.pack(side="right", fill="y", padx=10, pady=10)

        tk.Label(self.right_frame, text="Chat", fg=CHAT_COLOR, bg=BG_COLOR, font=FONT).pack(anchor="nw")

        self.chat_text = tk.Text(self.right_frame, height=20, width=40, bg="#1a1a1a",
                                 fg=CHAT_COLOR, font=FONT, relief="flat", wrap="word",
                                 insertbackground=CHAT_COLOR)
        self.chat_text.pack(pady=5)
        self.chat_text.config(state="disabled")

        self.chat_entry = tk.Entry(self.right_frame, bg="#262626", fg=CHAT_COLOR,
                                   font=FONT, insertbackground=CHAT_COLOR,
                                   highlightthickness=1, highlightbackground=CHAT_COLOR, relief="flat")
        self.chat_entry.pack(fill="x", pady=5)

        self.chat_entry.bind("<Return>", lambda e: self.send_msg())

        # =============== RIGHT: Salas ===================
        
        


        self.CLIENT_THREAD = threading.Thread(target=self.listen_server, daemon=False).start()


    def listen_server(self):
        msg = {'type': 'main_loop_sync', 'ready': True}
        n.send_pickle(self.client_socket, msg)
        while True:
            try:
                response= n.recv_pickle(self.client_socket)

                print(f"Received: {response}")

                if response['type'] == 'online_list':
                    self.after(0, lambda msg=response: self.update_players(msg))
                elif response['type'] == 'room_list':
                    self.after(0, lambda msg=response: self.update_room(msg))
                elif response['type'] == 'msg':
                    self.after(0, lambda msg=response: self.get_msg(msg))
                elif response['type'] == 'join_room_ack':
                    self.after(0, lambda msg=response: self.join_room_ack(msg))
                elif response['type'] == 'start_game':
                    self.after(0, lambda msg=response: self.start_game(msg))
                
            except Exception as e:
                print(f"Error idk wtf, error {e}")
                break
            

    def update_players(self, msg):
        players = msg['names']
        print(f"Updating players online list")
        self.players_listbox.delete(0, tk.END)
        for player in players:
            self.players_listbox.insert(tk.END, player)
        # self.client_socket.sendall(pickle.dumps({'type': 'update_players_sync','ready': True}))

    def update_room(self, msg):
        print(f"Updating room list, clients {msg['clients']}")
        room = msg['room']
        host = msg['host']
        self.rooms_listbox[room].delete(0, tk.END)
        for player in msg['clients']:
            if player == host:
                player += " (host)"
            self.rooms_listbox[room].insert(tk.END, player)

        if self.current_room == room and self.client_name == host: 
            self.isHost = True
            self.start_room.pack(pady=(20, 10), ipadx=10, ipady=5)





    def send_msg(self):

        if not self.chat_entry.get():
            return

        msg = {
            'type': 'msg',
            'content': self.chat_entry.get(),
            'username' : self.client_name
        }

        n.send_pickle(self.client_socket, msg)
        self.chat_entry.delete(0, tk.END)
        self.chat_text.config(state="normal")
        # self.chat_entry.focus_set()
        self.chat_text.insert(tk.END, "tu: " + msg['content'] + "\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)
    
    def get_msg(self, msg):
        self.chat_text.config(state="normal")
        self.chat_text.insert(tk.END, msg['username'] + ": " + msg['content'] + "\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def toggle_room(self, room):
        if self.current_room == None:
            self.join_room(room)
        elif self.current_room != room:
            messagebox.showerror("Error", "Ya estas en otra sala")  
        else:
            self.leave_room(room)

    def join_room(self, room):
        print("Joining room")
        msg = {
            'type': 'join_room',
            'room': room,
            'name': self.client_name
        }
        n.send_pickle(self.client_socket, msg)
        

    def join_room_ack(self, response):
        print(f"Joining room ack, msg {response}")
        if response['ok']:
            self.current_room = response['room']
        else :
            messagebox.showerror("Error", response['error'])



    def leave_room(self, room):
        msg = {
            'type': 'leave_room',
            'room': room,
            'name': self.client_name
        }
        if self.isHost:
            self.isHost = False
            self.start_room.pack_forget()
        self.current_room = None
        n.send_pickle(self.client_socket, msg)


    def start_room_action(self):
        msg = {
            'type': 'start_room',
            'room': self.current_room

        }
        n.send_pickle(self.client_socket, msg)


    def start_game(self, msg):
        if self.isHost:
            self.master.host = True
        self.master.host_ip = msg['ip']
        self.master.host_port = msg['port'] 
        self.master.num_players = msg['num_players']
        self.client_socket.close()
        self.show_frame(Snake.SnakeGameFrame)

     
            

# Ejecutar la app
if __name__ == "__main__":
    app = App(ConnectFrame)
    app.mainloop()

