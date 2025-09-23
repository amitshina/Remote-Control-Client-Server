import tkinter as tk
import client
import server
import threading
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) 
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def start_server():    
    root.destroy()

    # Create new window for displaying IP
    server_root = tk.Tk()
    server_root.title("Start a Server")
    server_root.geometry("300x150")
    server_root.resizable(False, False)
    
    # Find out my IP
    my_ip = get_local_ip()
    
    status_label = tk.Label(server_root, text=f"Wating for Connection", font=("Arial", 12))
    status_label.pack(pady=5)
    
    ip_label = tk.Label(server_root, text=f"Your IP Address is: {my_ip}", font=("Arial", 12))
    ip_label.pack(pady=5)
    
    def stop_server_button():
        try:
            server.server_instance.close_server()
        except Exception as e:
            print(f"Error stopping server {e}")
        server_root.destroy()
        main()
    
    btn_stop = tk.Button(server_root, text="Stop Server", font=("Arial", 12), command=stop_server_button)
    btn_stop.pack(pady=5)
    
    server_thread = threading.Thread(target=server.start_server, kwargs={'status_label':status_label}, daemon=True)
    server_thread.start()
    
    server_root.mainloop()

def server_closed():
    closed_root = tk.Tk()
    closed_root.title("Connect as Client")
    closed_root.geometry("300x150")
    closed_root.resizable(False, False)
    
    label = tk.Label(closed_root, text="Server Closed", font=("Arial", 12))
    label.pack(pady=15)
    
    def return_main():
        closed_root.destroy()
        main()
    
    btn_return = tk.Button(closed_root, text="Return", font=("Arial", 12), command=return_main)
    btn_return.pack(pady=15)

def open_client_window():
    root.destroy()

    # Create new window for client IP input
    client_root = tk.Tk()
    client_root.title("Connect as Client")
    client_root.geometry("300x150")
    client_root.resizable(False, False)

    label = tk.Label(client_root, text="Enter Server IP:", font=("Arial", 12))
    label.pack(pady=15)

    ip_entry = tk.Entry(client_root, font=("Arial", 12), width=20)
    ip_entry.pack(pady=5)

    def connect_client():
        ip = ip_entry.get().strip()
        client.start_client(ip=ip, tk_root=client_root)

    btn_connect = tk.Button(client_root, text="Connect", font=("Arial", 12), command=connect_client)
    btn_connect.pack(pady=15)

    client_root.mainloop()

def main():
    global root
    root = tk.Tk()
    root.title("Remote Viewer")
    root.geometry("300x150")
    root.resizable(False, False)

    label = tk.Label(root, text="Choose Mode:", font=("Arial", 14))
    label.pack(pady=20)

    btn_server = tk.Button(root, text="Server", font=("Arial", 12), width=10, command=start_server)
    btn_server.pack(pady=5)

    btn_client = tk.Button(root, text="Client", font=("Arial", 12), width=10, command=open_client_window)
    btn_client.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()