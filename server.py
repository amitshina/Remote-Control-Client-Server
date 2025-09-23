#requirements:
# pip install pyautogui pillow

import socket
import threading
import pyautogui
import io
from PIL import ImageGrab, ImageDraw
import struct
import time

last_sent=0

def handle_client(conn):
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
                    key = convert_key(key)
                    try:
                        pyautogui.keyDown(key)
                        print(f"Down {key}.")  
                    except:
                        print(f"[WARN] Unsupported key: {key}")
                elif cmd_type == b'UKeybr':
                    key = payload.rstrip(b'\x00').decode("utf-8")
                    key = convert_key(key)
                    try:
                        pyautogui.keyUp(key)
                        print(f"Up {key}.")
                    except:
                        print(f"[WARN] Unsupported key: {key}")
        except:
            pass
    
    # Listen for commands, run in the backround (as a deamon)
    threading.Thread(target=recv_commands, daemon=True).start()

    try:
        while True:
            # Send in ~30 FPS
            global last_sent
            now = time.time()
            if now-last_sent<0.03: 
                continue
            last_sent = now
            
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

def start_server(host='0.0.0.0', port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(1)
    print(f"[SERVER] Listening on {host}:{port}")
    while True:
        conn, addr = s.accept()
        print(f"[SERVER] Connected by {addr}")
        threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

def convert_key(key: str):
    map = {
        "Control_L": "ctrl",
        "Control_R": "ctrl",
        "Shift_L": "shift",
        "Shift_R": "shift",
        "Alt_L": "alt",
        "Alt_R": "alt",
    }
    return map.get(key, key)

if __name__ == "__main__":
    start_server()
