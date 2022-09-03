#!/bin/python3

import socket
import os
import time

addr = socket.getaddrinfo('0.0.0.0', 8080)[0][-1]

socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket1.bind(addr)
socket1.listen(1)

while True:
    conn, addr = socket1.accept()
    try:
        r = conn.recv(1024)
        r = r.decode().splitlines()[0].split(' ')

        req_method = r[0]
        req_data = r[1]
        req_data = req_data.strip('/')

        if (req_method == 'GET'):
            conn.send(b'HTTP/1.0 200 OK\r\n')

            if (req_data == 'scan.xml'):
                req_data = 'stations.xml'
                time.sleep(2) # simulate scanning by sleeping before sending response
            if (req_data == ''):
                req_data = 'index.html'
                conn.send(b'Content-type: text/html\r\n\r\n')
            else:
                req_data_ext = req_data.split('.')[-1]
                if (req_data_ext == 'html'):
                    conn.send(b'Content-type: text/html\r\n\r\n')
                elif (req_data_ext == 'svg'):
                    conn.send(b'Content-type: image/svg+xml\r\n\r\n')
                elif (req_data_ext == 'js'):
                    conn.send(b'Content-type: text/javascript\r\n\r\n')
                elif (req_data_ext == 'css'):
                    conn.send(b'Content-type: text/css\r\n\r\n')
                elif (req_data_ext == 'xml'):
                    conn.send(b'Content-type: text/xml\r\n\r\n')
                else:
                    raise ValueError

            file = open('web/' + req_data, 'rb')
            conn.sendall(file.read())
            file.close()
            conn.close()
        elif (req_method == 'PATCH'):
            req_data_split = req_data.split('/')
            if (len(req_data_split) == 3):
                if (req_data_split[0] == 'tune'):
                    if (req_data_split[1] == 'am'):
                        conn.send(b'HTTP/1.0 204 No Content\r\n\r\n')
                        conn.send(b'Content-Location: ' + req_data + '\r\n\r\n')
                    elif (req_data_split[1] == 'fm'):
                        conn.send(b'HTTP/1.0 204 No Content\r\n\r\n')
                        conn.send(b'Content-Location: ' + req_data + '\r\n\r\n')
                    else:
                        conn.send(b'HTTP/1.0 400 Bad Request\r\n\r\n')
            else:
                conn.send(b'HTTP/1.0 400 Bad Request\r\n\r\n')
        else:
            conn.send(b'HTTP/1.0 400 Bad Request\r\n\r\n')
            conn.close()
    except:
        conn.close()

socket1.close()
