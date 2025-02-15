import asyncio
import websockets
import threading
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk

connected_clients = set()

# WebSocket client setup
async def websocket_client():
    global ws
    try:
        ws = await asyncio.wait_for(websockets.connect("ws://192.168.0.178:8765"), timeout=20)
        connected_clients.add(ws)
        try:
            async for message in ws:
                update_chat_log(f"Friend: {message}")
        except Exception as e:
            print(f"WebSocket error: {e}")
            connected_clients.remove(ws)
    except asyncio.TimeoutError:
        print("Connection timed out during handshake")
    except Exception as e:
        print(f"An error occurred: {e}")

def start_websocket_client(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_client())

def update_chat_log(message):
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, f"{message}\n")
    chat_log.config(state=tk.DISABLED)
    chat_log.yview(tk.END)  # Auto-scroll to the end

# Create an event loop
loop = asyncio.new_event_loop()

client_thread = threading.Thread(target=start_websocket_client, args=(loop,), daemon=True)
client_thread.start()

# GUI setup
def close_app(event=None):
    if messagebox.askyesno("Quit", "Do you want to quit?"):
        root.destroy()

def send_message():
    message = chat_entry.get()
    if message:
        update_chat_log(f"{user_name}: {message}")
        chat_entry.delete(0, tk.END)
        asyncio.run_coroutine_threadsafe(send_ws_message(f"{user_name}: {message}"), loop)

async def send_ws_message(message):
    try:
        await asyncio.wait_for(ws.send(message), timeout=20)
    except asyncio.TimeoutError:
        print("Sending message timed out")
    except Exception as e:
        print(f"WebSocket error: {e}")

root = tk.Tk()
root.title("Chat App")
root.geometry("500x600")

# Set the icon for the application
icon_path = "cheesidibbl.png"  # Make sure the icon file is in the same directory as this script
root.iconphoto(False, tk.PhotoImage(file=icon_path))

# Prompt for user name
user_name = simpledialog.askstring("Name", "What is your name?", parent=root)
if not user_name:
    root.destroy()
    exit()

# Font setup
font_neon = tkFont.Font(family="MonaspaceNeon-Regular.otf", size=14)
style = ttk.Style()
style.configure("TButton", font=(font_neon, 14))
style.configure("TLabel", font=(font_neon, 14))
style.configure("TEntry", font=(font_neon, 14))
style.configure("TFrame", font=(font_neon, 14))  # for frames
style.configure("TCheckbutton", font=(font_neon, 14))  # for checkboxes

# Chat log with scrollbar
display_frame = tk.Frame(root)
display_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
chat_log = tk.Text(display_frame, state=tk.DISABLED, height=20, width=50, font=(font_neon, 12), wrap=tk.WORD)
chat_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar = tk.Scrollbar(display_frame, command=chat_log.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
chat_log.config(yscrollcommand=scrollbar.set)

# Chat entry
entry_frame = tk.Frame(root)
entry_frame.pack(pady=5, padx=10, fill=tk.X)
chat_entry = tk.Entry(entry_frame, width=40, font=(font_neon, 12))
chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
send_button = tk.Button(entry_frame, text="Send", command=send_message, font=(font_neon, 12))
send_button.pack(side=tk.RIGHT)

root.bind('<Return>', lambda event: send_message())
root.bind('<Escape>', close_app)

root.mainloop()
