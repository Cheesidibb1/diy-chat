import asyncio
import websockets
from datetime import datetime
import socket
import threading
import random
import sys
import os

connected_clients = set()
banned_ips = set()
admin_ips = set()
mod_ips = set()

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
# COMMANDS COMMANDS COMMANDS COMMANDS COMMANDS
            if message == "!ban":
                if ip_address in admin_ips:
                    ban_ip(ip_address)
                else: 
                    await websocket.send("System: You do not have permission to ban IP addresses.")
                continue
            elif message == "!unban":
                if ip_address in admin_ips:
                    unban_ip(ip_address)
                else:
                    await websocket.send("System: You do not have permission to unban IP addresses.")
                continue
            elif message.startswith("!rtd "):
                rtdnum = message.split(" ")[1]
                websocket.send(random(0, rtdnum))
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
        command = input("Enter command: ").strip()
        if command.startswith("!ban "):
            ip_address = command.split(" ")[1]
            ban_ip(ip_address)
        elif command.startswith("!unban "):
            ip_address = command.split(" ")[1]
            unban_ip(ip_address)
        elif command == "!banned":
            print(f"Banned IP addresses: {banned_ips}")
        elif command == "!clients":
            print(f"Connected clients: {connected_clients}")
        elif command.startswith("!admin "):
            ip_address = command.split(" ")[1]
            admin_ips.add(ip_address)
        elif command.startswith("!unadmin "):
            ip_address = command.split(" ")[1]
            admin_ips.discard(ip_address)
        elif command == "!admins":
            print(f"Admin IP adresses: {admin_ips}")
        elif command.startswith("!mod "):
            ip_adress = command.split(" ")[1]
            mod_ips.add(ip_adress)
        elif command.startswith("!unmod "):
            ip_adress = command.split(" ")[1]
            mod_ips.discard(ip_adress)
        elif command == "!mods":
            print(f"Moderator IP adresses: {mod_ips}")
        elif command == "!help":
            print("Available commands:")
            print("!ban <ip_address> - Ban an IP address")
            print("!unban <ip_address> - Unban an IP address")
            print("!banned - List banned IP addresses")
            print("!clients - List connected clients")
            print("!admin <ip adress> - Make an IP address an admin")
            print("!unadmin <ip adress> - Remove admin status from an IP address")
            print("!admins - List admin IP addresses")
            print("!mod <ip adress> - Make an IP address a moderator")
            print("!unmod <ip adress> - Remove moderator status from an IP address")
            print("!help - Show available commands")
            print("!exit - Exit the command handler")
        elif command == "!exit":
            print("Exiting command handler.")
            break
        else:
            print("Unknown command.")

# Start the server and command handler
server_thread = threading.Thread(target=lambda: asyncio.run(main()), daemon=True)
server_thread.start()

handle_commands()
