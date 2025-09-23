import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import io
import struct
import time
import pyautogui

class Client:
    def __init__(self, port=5000, host=''): # Defualt port: 5000
        if not host: host = input("Enter your IP Address: ")
        
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
        
        self.last_sent = 0
        
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
        now = time.time()
        if now - self.last_sent < 0.07:
            return
        self.last_sent = now
        
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
        key = event.char
        if not key or not key.isprintable():
            key = event.keysym
        # print(f"char: '{event.char}', and keysym: '{event.keysym}', chosen: '{key}'")
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

class Server:
    def __init__(self, host='0.0.0.0', port=5000):
        self.last_sent=0
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(1)
        print(f"[SERVER] Listening on {host}:{port}")
        while True:
            conn, addr = s.accept()
            print(f"[SERVER] Connected by {addr}")
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self,conn):
        # Send screen resolution
        width, height = pyautogui.size()
        conn.sendall(width.to_bytes(4, 'big') + height.to_bytes(4, 'big'))
        
        # Recives mouse cordinates
        def recv_commands():
            try:
                while True:
                    # Read 38 bytes: 6 byte type + 32 bytes payload (when the payload does'nt matter, zeros are sent)
                    data = conn.recv(38)
                    if not data:
                        break
                    # print(data)
                    cmd_type = data[0:6]  # b'MMouse' for move, b'LMouse' left click, b'RMouse' right click, DMouse and UMouse for click up and down
                    payload = data[6:]
                    if cmd_type == b'MMouse':
                        x, y = struct.unpack(">II", payload[:8])
                        pyautogui.moveTo(x, y, duration=0.00001)
                    elif cmd_type == b'LMouse':
                        pyautogui.click(button='left')
                    elif cmd_type == b'RMouse':
                        pyautogui.click(button='right')
                    elif cmd_type == b'DMouse':
                        pyautogui.mouseDown(button='left')
                    elif cmd_type == b'UMouse':
                        pyautogui.mouseUp(button='left')
                    elif cmd_type == b'DKeybr':
                        key = payload.rstrip(b'\x00').decode("utf-8")
                        key = self.convert_key(key)
                        try:
                            pyautogui.keyDown(key)
                            print(f"Down {key}.")  
                        except:
                            print(f"[WARN] Unsupported key: {key}")
                    elif cmd_type == b'UKeybr':
                        key = payload.rstrip(b'\x00').decode("utf-8")
                        key = self.convert_key(key)
                        try:
                            pyautogui.keyUp(key)
                            print(f"Up {key}.")
                        except:
                            print(f"[WARN] Unsupported key: {key}")
            except:
                pass
        
        # Listen for commands, run in the backround (as a deamon)
        threading.Thread(target=recv_commands, daemon=True).start()
        
        # Send screen:
        try:
            while True:
                # Send in ~30 FPS
                now = time.time()
                if now-self.last_sent<0.03: 
                    continue
                self.last_sent = now
                
                # Capture the screen (without the mouse cursor)
                img = ImageGrab.grab()
                
                # Draw the mouse cursor on the screenshot as a red dot
                cursor_x, cursor_y = pyautogui.position()
                draw = ImageDraw.Draw(img)
                cursor_size = 5
                draw.ellipse((cursor_x - cursor_size, cursor_y - cursor_size,cursor_x + cursor_size, cursor_y + cursor_size), fill="red")
                
                # Convert to JPEG and send to the client
                buf = io.BytesIO()
                img.save(buf, format='JPEG')
                data = buf.getvalue()
                
                # Send the image and its size
                conn.sendall(len(data).to_bytes(8, 'big') + data)
        except Exception as e:
            print(f"Exeption: {e}, Connection Closed, Wating for a new connection")
        finally:
            # Close the connection in an error acuurs
            conn.close()

    def convert_key(self, key: str):
        map = {
            "Control_L": "ctrl",
            "Control_R": "ctrl",
            "Shift_L": "shift",
            "Shift_R": "shift",
            "Alt_L": "alt",
            "Alt_R": "alt",
        }
        return map.get(key, key)

def main():
    x = int(input("Press 1 for server, 2 for client: \n"))
    
    if x==1: Server()
    elif x==2: Client()
    else: print("unrecognized")

if __name__=="__main__": main()