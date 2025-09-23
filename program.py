import socket
import threading
import tkinter as tk
from PIL import Image, ImageTk, ImageGrab, ImageDraw
import io
import struct
import time
import pyautogui

import client
import server

def main():
    x = int(input("Press 1 for server, 2 for client: \n"))
    
    if x==1: server.start_server()
    elif x==2: client.start_client()
    else: print("unrecognized")

if __name__=="__main__": main()