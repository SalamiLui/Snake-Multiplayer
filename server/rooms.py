class Room:
    def __init__(self):
        self.clients = []
        self.host = None

    def add_client(self, client) -> bool:
        if len(self.clients) >= 4:
            return False
        if self.host is None:
            self.host = client
        self.clients.append(client)
        return True

    def remove_client(self, client):
        self.clients.remove(client)
        if client == self.host:
            if len(self.clients) > 0:
                self.host = self.clients[0]
            else:
                self.host = None

    def clean(self):
        self.clients = []
        self.host = None


