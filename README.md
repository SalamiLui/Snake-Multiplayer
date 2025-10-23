# Snake Multiplayer

Simple snake game multiplayer in python using sockets

## Architecture

In the lobby the connection is client-server, once the room starts the conecion becomes p2p between players

## How to play 

1. Start the server 

```bash
python server.py
```

2. Start the client 

```bash
python lobby.py 
```

3. Connect to the server
In the UI u will be asked for ip and port, defaults are 127.0.0.1 and 5555

4. play 

## Considerations

This game was made with pickle for serialization, so it's not recommended to run this game in no secure environment 

