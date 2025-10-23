import socket, struct, pickle


def send_pickle(sock, obj):
    data = pickle.dumps(obj)
    size = struct.pack("!I", len(data))
    sock.sendall(size+ data)


def recv_pickle(sock):
    def recv_n(sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                raise ConnectionError("Socket cerrado")
            data += packet
        return data

    raw_len = recv_n(sock, 4)
    msg_len = struct.unpack('!I', raw_len)[0]
    data = recv_n(sock, msg_len)
    return pickle.loads(data)   
