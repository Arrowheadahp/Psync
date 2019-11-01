import socket
import pickle
import os
from time import sleep
from datetime import datetime
import threading

headersize = 8
socketsize = 1024


def getport():
    #return ('conn', 1234, 1996)
    return ('bind', 1234, 1996)




def logwrite(s, f):
    log = f'{s},{f},{datetime.now()}'
    print (log)
    with open('log.txt', 'a') as logfile:
        logfile.write(log)


def socket_send(sock, msg):
    global headersize
    lmsg = bytes(f"{len(msg):<{headersize}}",
                 'utf-8')
    if type(msg)!=type(lmsg):
        msg = bytes(msg, 'utf-8')
    sock.send(lmsg + msg)
    sleep(0.1)

def socket_recv(sock):
    global headersize
    msglen = int(sock.recv(headersize))
    return sock.recv(msglen)


def getdir():
    path = os.getcwd()

    files = []
    # r=root, d=directories, f = files
    for _, _, f in os.walk(path):
        for file in f:
            files.append(file)
    
    return set(files)



def save_part(sock, d):
    lc = int(sock.recv(headersize))
    with open(d, 'wb') as file:
        for _ in range(lc):
            file.write(socket_recv(sock))



def send_part(sock, d):
    socket_send(sock, d)
    with open(d, 'rb') as f:
        fullcontent = f.read()
    content = [fullcontent[i: i+socketsize] for i in range(0, len(fullcontent), socketsize)]
    lc = len(content)
    sock.send(bytes(f"{lc:<{headersize}}", 'utf-8'))
    
    for c in content:
        socket_send(sock, c)


def recieve_dir(sock):
    #print('Recieving directory started')
    num = int(sock.recv(headersize))
    for _ in range(num):
        d = socket_recv(sock)
        save_part(sock, d)
        logwrite('recv', d)
        


def send_dir(sock, should_send):
    #print('Sending directory started')
    sock.send(bytes(f"{len(should_send):<{headersize}}", 'utf-8'))
    for d in should_send:
        send_part(sock, d)
        logwrite('sent', d)


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
    L.sort(key = lambda i : i.split('.')[-1][0], reverse = True)
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
    recvthread.start()

    #print('done')
    break
