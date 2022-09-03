#!/bin/python3

import socket
import os
import time

addr = socket.getaddrinfo('0.0.0.0', 1234)[0][-1]

socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket1.bind(addr)
socket1.listen(1)

with open("test.wav", 'rb') as file:
    while True:
        conn, addr = socket1.accept()
        try:
            r = conn.recv(1024)
            conn.send(b'HTTP/1.0 200 OK\r\n' \
                      b'Access-Control-Allow-Origin: *\r\n' \
                      b'Content-type: audio/wav\r\n\r\n')
            while True:
                conn.sendall(file.read(3000))
                time.sleep(0.1) # simulate time taken to acquire 100ms of samples
            conn.close()
        except:
            file.seek(0,0)
            conn.close()

    file.seek(0,0)

socket1.close()
