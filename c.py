import socket
import pickle
import os
from time import sleep
import threading

headersize = 16


def getport():
    #return ('conn', 1234, 1996)
    return ('bind', 1234, 1996)



def socket_send(sock, msg):
    global headersize
    fmsg = bytes(f"{len(msg):<{headersize}}",
                 'utf-8')
    if type(msg)!=type(fmsg):
        msg = bytes(msg, 'utf-8')

    fmsg = fmsg+msg
    
    sock.send(fmsg)
    sleep(0.1)

def socket_recv(sock):
    global headersize
    full_msg = b''
    new_msg = True
    while True:
        msg = sock.recv(headersize)
        if new_msg:
            msglen = int(msg)
            new_msg = False
        else:
            full_msg += msg

        if len(full_msg) == msglen:
            #print(full_msg)
            return full_msg


def getdir():
    path = os.getcwd()

    files = []
    # r=root, d=directories, f = files
    for _, _, f in os.walk(path):
        for file in f:
            files.append(file)
    
    return set(files)



def save_part(sock, d):
    content = ''
    content = socket_recv(sock)
    with open(d, 'wb') as file:
        file.write(content)



def send_part(sock, d):
    socket_send(sock, d)
    with open(d, 'rb') as f:
        content = f.read()
    print ('Sending',d)
    socket_send(sock, content)
    print (d,'sent')


def recieve_dir(sock):
    print('Recieving directory started')
    num = int(sock.recv(headersize))
    for _ in range(num):
        d = socket_recv(sock)
        print ('Recieving',d)
        save_part(sock, d)
        print (d,'recieved')


def send_dir(sock, should_send):
    print('Sending directory started')
    sock.send(bytes(f"{len(should_send):<{headersize}}",
                    'utf-8'))
    for d in should_send:
        send_part(sock, d)


def bindport(sock, port):
    sock.bind((socket.gethostname(), port))
    print (port,'bound')
    sock.listen(5)
    boundsock, address = sock.accept()
    print('connection made with', address)
    return boundsock

def connport(sock, port):
    while True:
        try:
            sock.connect((socket.gethostname(), port))
            break
        except:
            sleep(.1)
    print(port,'connected')
    return sock


sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



def prioritise(S):
    L = list(S)
    L.sort(key = lambda i : i.split('.')[-1][0])
    return L



while True:
    command, port1, port2 = getport()

    if command == 'bind':
        serversock1 = bindport(sock1, port1)
        serversock2 = bindport(sock2, port2)
        
    
        socket_send(serversock1, pickle.dumps(getdir()))
        print('server dir sent:')

        should_send = pickle.loads(socket_recv(serversock1))
        print('should send recieved:', should_send)

        sendthread = threading.Thread(target = send_dir, args = (serversock1, should_send, ))
        recvthread = threading.Thread(target = recieve_dir, args = (serversock2, ))

    elif command == 'conn':
        clientsock1 = connport(sock1, port1)
        clientsock2 = connport(sock2, port2)
        
        recv_dir = pickle.loads(socket_recv(clientsock1))
        print('server dir recieved')

        curr_dir = getdir()
        should_recv = prioritise(recv_dir - curr_dir)
        should_send = prioritise(curr_dir - recv_dir)

        socket_send(clientsock1, pickle.dumps(should_recv))
        print('should recieve sent:', should_recv)

        sendthread = threading.Thread(target = send_dir, args = (clientsock2, should_send, ))
        recvthread = threading.Thread(target = recieve_dir, args = (clientsock1, ))
    
    sendthread.start()
    sleep(0.1)
    recvthread.start()

    print('done')
    break
