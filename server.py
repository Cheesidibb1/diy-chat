import asyncio
import websockets
from datetime import datetime
import socket
import threading

connected_clients = set()
banned_ips = set()

async def echo(websocket, path):
    ip_address = websocket.remote_address[0]
    if ip_address in banned_ips:
        print(f"Banned IP {ip_address} attempted to connect.\n")
        await websocket.send("System: You have been banned.")
        await websocket.close()
        return

    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    try:
        async for message in websocket:
            # Log the message with a timestamp and IP address
            with open("chat_log.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"[{timestamp}] {ip_address}: {message}\n")
            
            print(f"Received message from {websocket.remote_address}: {message}")
            
            # Broadcast the message to all connected clients except the sender
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
                    print(f"Sent message to {client.remote_address}")
    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def main():
    # Create a WebSocket server, listening on 0.0.0.0:8765
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    async with websockets.serve(echo, "0.0.0.0", 8765):
        print(f"Server is running at ws://{local_ip}:8765")
        await asyncio.Future()  # Run forever

def ban_ip(ip_address):
    banned_ips.add(ip_address)
    print(f"IP address {ip_address} has been banned.")

def unban_ip(ip_address):
    banned_ips.discard(ip_address)
    print(f"IP address {ip_address} has been unbanned.")

def handle_commands():
    while True:
        command = input("Enter command (ban <ip> / unban <ip> / exit): ").strip()
        if command.startswith("ban "):
            ip_address = command.split(" ")[1]
            ban_ip(ip_address)
        elif command.startswith("unban "):
            ip_address = command.split(" ")[1]
            unban_ip(ip_address)
        elif command == "exit":
            print("Exiting command handler.")
            break
        else:
            print("Unknown command.")

# Start the server and command handler
server_thread = threading.Thread(target=lambda: asyncio.run(main()), daemon=True)
server_thread.start()

handle_commands()
