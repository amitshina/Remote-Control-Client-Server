#requirements:
#pip install pillow

import socket
import tkinter as tk
from PIL import Image, ImageTk
import io
import struct
import time

last_sent = 0

class RemoteViewer:
    def __init__(self, host='127.0.0.1', port=5000): # Defualt address: localhost:5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        
        # Recives and sets server screen resolution
        data = self.sock.recv(8)
        self.server_width = int.from_bytes(data[:4], 'big')
        self.server_height = int.from_bytes(data[4:], 'big')
        print(f"Server resolution: {self.server_width}x{self.server_height}")

        self.root = tk.Tk() 
        
        self.root.geometry(f"{self.server_width}x{self.server_height}")
        self.root.resizable(False, False)  # Disable resizing
        
        self.label = tk.Label(self.root) 
        self.label.pack()

        # Commend Actions
        self.label.bind("<Motion>", self.mouse_move)
        self.label.bind("<Button-1>", self.mouse_click)
        self.label.bind("<Button-3>", self.mouse_click)
        self.label.bind("<ButtonPress-1>", self.left_down)
        self.label.bind("<ButtonRelease-1>", self.left_up)
        self.label.bind("<KeyPress>", self.keyboard_down)
        self.label.bind("<KeyRelease>", self.keyboard_up)
        
        self.label.focus_set()
        
        # Update Screen
        self.update_frame()
        self.root.mainloop()

    def update_frame(self):
        # Recives image size
        size_data = self.sock.recv(8)
        if not size_data:
            self.root.destroy()
            return
        size = int.from_bytes(size_data, 'big')

        # Receive image bytes
        data = b''
        while len(data) < size:
            packet = self.sock.recv(size - len(data))
            if not packet:
                return
            data += packet

        img = Image.open(io.BytesIO(data))
        img_tk = ImageTk.PhotoImage(img)

        self.label.config(image=img_tk)
        self.label.image = img_tk

        self.root.after(30, self.update_frame)  # ~30 FPS

    def mouse_move(self, event):
        global last_sent
        now = time.time()
        if now - last_sent < 0.07:
            return
        last_sent = now
        
        try:
            self.sock.sendall(b'MMouse' + struct.pack(">II", event.x, event.y).ljust(32, b'\x00'))
        except:
            pass
    
    # When clicking the mouse
    def mouse_click(self, event):
        try:
            if event.num == 1:  # left click
                self.sock.sendall(b'LMouse' + b'\x00'*32)
            elif event.num == 3:  # right click
                self.sock.sendall(b'RMouse' + b'\x00'*32)
        except:
            pass
    
    # When selectiong stuff with the mouse:
    def left_down(self, event):
        try:
            self.sock.sendall(b'DMouse' + b'\x00'*32)
        except:
            pass
    def left_up(self, event):
        try:
            self.sock.sendall(b'UMouse' + b'\x00'*32)
        except:
            pass
    
    def get_key(self, event):
        key = event.keysym
        if event.char and event.char.strip() != "":
            key =  event.char
        if not key or key == "":
            key = event.keysym
        if not key:
            return None
        return key
    
    def keyboard_down(self,event):
        key = self.get_key(event)
        try:
            key_bytes = key.encode('utf-8')[:32].ljust(32, b'\x00')
            self.sock.sendall(b'DKeybr' + key_bytes)
            print("[SEND DOWN]", key)
        except:
            pass
    
    def keyboard_up(self,event):
        key = self.get_key(event)
        try:
            key_bytes = key.encode('utf-8')[:32].ljust(32, b'\x00') 
            self.sock.sendall(b'UKeybr' + key_bytes)
            print("[SEND UP]", key) 
        except:
            pass

if __name__ == "__main__":
    server_ip = input("Enter your IP Address: ")
    RemoteViewer(server_ip, 5000)
