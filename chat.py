import asyncio
import websockets
import threading
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

connected_clients = set()

# WebSocket client setup
async def websocket_client():
    global ws
    async with websockets.connect("ws://192.168.0.178:8765") as ws:
        connected_clients.add(ws)
        try:
            async for message in ws:
                chat_log.config(state=tk.NORMAL)
                chat_log.insert(tk.END, f"Friend: {message}\n")
                chat_log.config(state=tk.DISABLED)
        except:
            connected_clients.remove(ws)

def start_websocket_client(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_client())

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
        chat_log.config(state=tk.NORMAL)
        chat_log.insert(tk.END, f"You: {message}\n")
        chat_log.config(state=tk.DISABLED)
        chat_entry.delete(0, tk.END)
        asyncio.run_coroutine_threadsafe(send_ws_message(message), loop)

async def send_ws_message(message):
    async with websockets.connect("ws://192.168.0.178:8765") as ws:
        await ws.send(message)

root = tk.Tk()
root.title("Chat App")
root.geometry("500x600")

# Font setup
font_neon = tkFont.Font(family="MonaspaceNeon-Regular.otf", size=14)
style = ttk.Style()
style.configure("TButton", font=(font_neon, 14))
style.configure("TLabel", font=(font_neon, 14))
style.configure("TEntry", font=(font_neon, 14))
style.configure("TFrame", font=(font_neon, 14))  # for frames
style.configure("TCheckbutton", font=(font_neon, 14))  # for checkboxes

# Chat log
display_frame = tk.Frame(root)
display_frame.pack(pady=10)
chat_log = tk.Text(display_frame, state=tk.DISABLED, height=20, width=50, font=(font_neon, 12))
chat_log.pack()

# Chat entry
chat_entry = tk.Entry(root, width=40, font=(font_neon, 12))
chat_entry.pack(pady=5)

send_button = tk.Button(root, text="Send", command=send_message, font=(font_neon, 12))
send_button.pack(pady=5)

root.bind('<Return>', lambda event: send_message())
root.bind('<Escape>', close_app)

root.mainloop()
