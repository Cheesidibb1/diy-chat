import asyncio
import websockets
from datetime import datetime, timedelta
import socket
import threading
import random
import os

# Global sets to manage clients and IP addresses
connected_clients = set()
banned_ips = set()
admin_ips = set()
mod_ips = set()
kick_ips = {}

# File paths for storing admin, moderator, banned, and kicked IP addresses
ADMIN_FILE = "admins.txt"
MOD_FILE = "mods.txt"
BANNED_FILE = "banned.txt"
KICKED_FILE = "kicked.txt"

def load_ips(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return set(line.strip() for line in file)
    return set()

def save_ips(file_path, ip_set):
    with open(file_path, "w") as file:
        for ip in ip_set:
            file.write(f"{ip}\n")

def load_kick_ips(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return {line.split(",")[0]: datetime.fromisoformat(line.split(",")[1].strip()) for line in file}
    return {}

def save_kick_ips(file_path, ip_dict):
    with open(file_path, "w") as file:
        for ip, end_time in ip_dict.items():
            file.write(f"{ip},{end_time.isoformat()}\n")

# Load admin, moderator, banned, and kicked IP addresses from files
admin_ips = load_ips(ADMIN_FILE)
mod_ips = load_ips(MOD_FILE)
banned_ips = load_ips(BANNED_FILE)
kick_ips = load_kick_ips(KICKED_FILE)

async def addlog(ip_address, message):
    with open("chat_log.txt", "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {ip_address}: {message}\n")

async def echo(websocket, path):
    ip_address = websocket.remote_address[0]
    await addlog(ip_address, "Connected")
    
    # Check if the IP address is banned
    if ip_address in banned_ips:
        print(f"Banned IP {ip_address} attempted to connect.\n")
        await websocket.send("System: You have been banned.")
        await websocket.close()
        return
    
    # Check if the IP address is kicked
    if ip_address in kick_ips:
        kick_end_time = kick_ips[ip_address]
        if datetime.now() < kick_end_time:
            print(f"Kicked IP {ip_address} attempted to connect.\n")
            await websocket.send("System: You have been kicked.")
            await websocket.close()
            return
    
    connected_clients.add(websocket)
    print(f"Client connected: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            # Log the message with a timestamp and IP address
            await addlog(ip_address, message)
            print(f"Received message from {websocket.remote_address}: {message}")
            
            # Parse the message to extract the username and command
            if ": " in message:
                user_name, command = message.split(": ", 1)
            else:
                continue
            
            # Handle client commands
            if command.startswith("!ban "):
                if ip_address in admin_ips:
                    target_ip = command.split(" ")[1]
                    ban_ip(target_ip)
                    await websocket.send(f"System: IP address {target_ip} has been banned.")
                else:
                    await websocket.send("System: You do not have permission to ban IP addresses.")
                continue
            
            elif command.startswith("!unban "):
                if ip_address in admin_ips:
                    target_ip = command.split(" ")[1]
                    unban_ip(target_ip)
                    await websocket.send(f"System: IP address {target_ip} has been unbanned.")
                else:
                    await websocket.send("System: You do not have permission to unban IP addresses.")
                continue
            
            elif command.startswith("!kick "):
                if ip_address in admin_ips or ip_address in mod_ips:
                    target_ip = command.split(" ")[1]
                    kick_end_time = datetime.now() + timedelta(minutes=int(command.split(" ")[2]))
                    kick_ips[target_ip] = kick_end_time
                    save_kick_ips(KICKED_FILE, kick_ips)
                    for client in connected_clients:
                        if client.remote_address[0] == target_ip:
                            await client.send("System: You have been kicked.")
                            await client.close()
                            break
                    await websocket.send(f"System: IP address {target_ip} has been kicked until {kick_end_time}.")
                else:
                    await websocket.send("System: You do not have permission to kick IP addresses.")
                continue
            
            elif command.startswith("!rtd "):
                try:
                    rtdnum = int(command.split(" ")[1])
                    result = random.randint(0, rtdnum)
                    await websocket.send(f"System: RTD result: {result}")
                except Exception as e:
                    print(f"Error processing !rtd command: {e}")
                    await websocket.send("System: Invalid RTD command.")
                continue
            
            elif command == "!rps":
                rpc = random.choice(["rock", "paper", "scissors"])
                await websocket.send(f"System: RPC result: {rpc}")
                continue
            
            elif command.startswith("!admin "):
                if ip_address in admin_ips:
                    target_ip = command.split(" ")[1]
                    admin_ips.add(target_ip)
                    save_ips(ADMIN_FILE, admin_ips)
                    await websocket.send(f"System: IP address {target_ip} has been made an admin.")
                    await notify_user(target_ip, "You have been made an admin.")
                else:
                    await websocket.send("System: You do not have permission to make other users admins.")
                continue
            
            elif command.startswith("!unadmin "):
                if ip_address in admin_ips:
                    target_ip = command.split(" ")[1]
                    if target_ip in admin_ips:
                        admin_ips.discard(target_ip)
                        save_ips(ADMIN_FILE, admin_ips)
                        await websocket.send(f"System: IP address {target_ip} has been removed from admins.")
                        await notify_user(target_ip, "You have been removed from admins.")
                    else:
                        await websocket.send(f"System: IP {target_ip} is not an admin.")
                else:
                    await websocket.send("System: You do not have permission to remove admin status from other users.")
                continue
            
            elif command.startswith("!mod "):
                if ip_address in admin_ips:
                    target_ip = command.split(" ")[1]
                    if target_ip not in mod_ips:
                        mod_ips.add(target_ip)
                        save_ips(MOD_FILE, mod_ips)
                        await websocket.send(f"System: IP address {target_ip} has been made a moderator.")
                        await notify_user(target_ip, "You have been made a moderator.")
                else:
                    await websocket.send("System: You do not have permission to make other users moderators.")
                continue
            
            elif command.startswith("!unmod "):
                if ip_address in admin_ips:
                    target_ip = command.split(" ")[1]
                    if target_ip in mod_ips:
                        mod_ips.discard(target_ip)
                        save_ips(MOD_FILE, mod_ips)
                        await websocket.send(f"System: IP address {target_ip} has been removed from moderators.")
                        await notify_user(target_ip, "You have been removed from moderators.")
                else:
                    await websocket.send("System: You do not have permission to remove moderator status from other users.")
                continue
            
            elif command == "!clients":
                if ip_address in admin_ips or ip_address in mod_ips:
                    await websocket.send(f"System: Connected clients: {connected_clients}")
                else:
                    await websocket.send("System: You do not have permission to view connected clients.")
                continue

            # Broadcast the message to all connected clients except the sender
            for client in connected_clients:
                if client != websocket:
                    await client.send(message)
    
    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    
    finally:
        connected_clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}")

async def notify_user(ip_address, message):
    for client in connected_clients:
        if client.remote_address[0] == ip_address:
            await client.send(f"System: {message}")
            break

async def main():
    # Create a WebSocket server, listening on 0.0.0.0:8765
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    async with websockets.serve(echo, "0.0.0.0", 8765):
        print(f"Server is running at ws://{local_ip}:8765")
        await asyncio.Future()  # Run forever

def ban_ip(ip_address):
    banned_ips.add(ip_address)
    save_ips(BANNED_FILE, banned_ips)
    print(f"IP address {ip_address} has been banned.")

def unban_ip(ip_address):
    banned_ips.discard(ip_address)
    save_ips(BANNED_FILE, banned_ips)
    print(f"IP address {ip_address} has been unbanned.")

def handle_commands():
    while True:
        command = "nope"
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
            save_ips(ADMIN_FILE, admin_ips)
            print(f"IP address {ip_address} has been made an admin.")
        elif command.startswith("!unadmin "):
            ip_address = command.split(" ")[1]
            admin_ips.discard(ip_address)
            save_ips(ADMIN_FILE, admin_ips)
            print(f"IP address {ip_address} has been removed from admins.")
        elif command == "!admins":
            print(f"Admin IP addresses: {admin_ips}")
        elif command.startswith("!mod "):
            ip_address = command.split(" ")[1]
            mod_ips.add(ip_address)
            save_ips(MOD_FILE, mod_ips)
            print(f"IP address {ip_address} has been made a moderator.")
        elif command.startswith("!unmod "):
            ip_address = command.split(" ")[1]
            mod_ips.discard(ip_address)
            save_ips(MOD_FILE, mod_ips)
            print(f"IP address {ip_address} has been removed from moderators.")
        elif command.startswith("!kick "):
            if ip_address in admin_ips or ip_address in mod_ips:
                target_ip = command.split(" ")[1]
                kick_end_time = datetime.now() + timedelta(minutes=int(command.split(" ")[2]))
                kick_ips[target_ip] = kick_end_time
                save_kick_ips(KICKED_FILE, kick_ips)
                print(f"IP address {target_ip} has been kicked until {kick_end_time}.")
        elif command == "!mods":
            print(f"Moderator IP addresses: {mod_ips}")
        elif command == "!help":
            print("Available commands:")
            print("!ban <ip_address> - Ban an IP address")
            print("!unban <ip_address> - Unban an IP address")
            print("!banned - List banned IP addresses")
            print("!clients - List connected clients")
            print("!admin <ip_address> - Make an IP address an admin")
            print("!unadmin <ip_address> - Remove admin status from an IP address")
            print("!admins - List admin IP addresses")
            print("!mod <ip_address> - Make an IP address a moderator")
            print("!unmod <ip_address> - Remove moderator status from an IP address")
            print("!kick <ip_address> <minutes> - Kick an IP address for a specified number of minutes")
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





