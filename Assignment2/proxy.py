import socket
import os
from threading import *
from _thread import start_new_thread
import threading
import time
import sys
import re
import queue
import pickle
import signal


MAX_CACHE_SIZE = 15

global blocked_urls,blocked_words
blocked_urls = []
blocked_words = []
cache = {}
#q = queue.Queue(maxsize=MAX_CACHE_SIZE)
fifo = []
lst = []

def signal_handler(sig,frame):
    sys.exit()


def admin_panel():

    global cache_type
    while True:

        print('------------------------------------------------------------------')
        print('1. Turn on Proxy     2. Configure Filters        3.Exit')

        x = int(input())
        if x==1:
            print('1. FIFO CACHING      2. LRU CACHING')
            y = int(input())
            cache_type = y
            return
        
        elif x == 3:
            sys.exit()

        else:

            if os.path.getsize("b_url.pickle") > 0:
                with open("b_url.pickle", "rb") as f:
                    blocked_urls = pickle.load(f)
            else:
                blocked_urls = []

            if os.path.getsize("b_word.pickle") > 0:
                with open("b_word.pickle", "rb") as f:
                    blocked_words = pickle.load(f)
            else:
                blocked_words = []
            
            print('1. Block URL    2. Block Keyword     3. Delete URL    4. Delete keyword')
            x = int(input())

            if x == 1:

                print('Enter a url you wish to block/filter')
                url = input()
                blocked_urls.append(url)
            elif x == 2:
                print('Enter Keyword')
                word = input()
                blocked_words.append(word)
            elif x == 3:
                print(blocked_urls)
                print('Enter url')
                v = input()
                blocked_urls.remove(v)
                print('URL removed from blocked urls...')
            elif x == 4:
                print(blocked_words)
                print('Enter keyword')
                v = input()
                blocked_words.remove(v)
                print('Keyword removed from blocked keywords...')

            with open("b_url.pickle","wb") as f:
                pickle.dump(blocked_urls,f)
            with open("b_word.pickle","wb") as f:
                pickle.dump(blocked_words,f)
def check_blockedUrl(url):

    for i in blocked_urls:
        if re.search(i,url):
            return True
    
    return False


def check_blockedWords(word):


    for i in blocked_words:
        
        if re.search(i,word,re.IGNORECASE):
            return True

    return False
def parse_http(request):
    
    lines = request.split("\r\n")
    first_line = lines[0]

    method, uri, version = first_line.split()
    
    if method == 'CONNECT':
        return 1

    server_address = uri.split('/')[2]
    print(server_address)
    return server_address

def get_ip(address):

    ip = address
    port = ''

    addr = socket.gethostbyname(ip)
    return addr


def get_data(server_ip,client,address,request,server_address):


    if check_blockedUrl(server_address) or check_blockedWords(server_address):

        reply = "HTTP/1.1 403 Forbidden\r\n\r\n"
        client.sendall(reply.encode())
        client.close()
        return


    if os.path.getsize("cache.pickle") > 0:

        with open("cache.pickle", "rb") as f:
            cache = pickle.load(f)
    else:
        cache = {}

    if os.path.getsize("q.pickle") > 0:

        with open("q.pickle", "rb") as f:
            fifo = pickle.load(f)
    else:
        #q = queue.Queue(maxsize=MAX_CACHE_SIZE)
        fifo = []

    if os.path.getsize("lst.pickle") > 0:

        with open("lst.pickle", "rb") as f:
            lst = pickle.load(f)
    else:
        lst = []
    
    request = request.encode("utf-8")
    if request in cache:
        print('Cache Hit')

        if cache_type == 2:
            lst.remove(request)
            lst.append(request)

        client.send(cache[request])
        return

    print('Cache Miss')
    ip = server_ip
    port = 80
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((ip,port))

    s.send(request)
    data = s.recv(4096)
    
    lock = threading.Lock()

    if cache_type == 1:
        lock.acquire()
        cache[request] = data
        fifo.append(request)
        print('data put in cache')
        if len(fifo) > MAX_CACHE_SIZE:
            oldest_url = fifo.pop(0)
            del cache[oldest_url]

        lock.release()

    elif cache_type == 2:
        lock.acquire()
        cache[request] = data
        lst.append(request)
        
        if len(lst) > MAX_CACHE_SIZE:
            lru_url = lst.pop(0)
            del cache[lru_url]

        lock.release()
    client.send(data)
    
    # while True:

    #     try:

    #         request = client.recv(8192)
    #         s.send(request)

    #     except Exception as e:
    #         break

    #     try:

    #        response = s.recv(8192)
    #        cache[request] = response
    #        client.send(response)
    #     except Exception as e:
    #         break 
   

    with open("cache.pickle","wb") as f:
        pickle.dump(cache,f)

    with open("q.pickle","wb") as f:
        pickle.dump(fifo,f)
    with open("lst.pickle","wb") as f:
        pickle.dump(lst,f)

    s.close()
    client.close()


def handle_https(client,address,request):


    dest = request.split()[1]
    destination = dest.split(':')[0]
    dest_port = int(dest.split(':')[1])

    if check_blockedUrl(destination) or check_blockedWords(destination):

        reply = "HTTP/1.1 403 Forbidden\r\n\r\n"
        client.sendall(reply.encode())
        client.close()
        return


    destination = socket.getaddrinfo(destination,dest_port)
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #dest_socket.connect((destination, dest_port))
   
   
    destination = destination[0][4][0]
    proxy.connect((destination,dest_port))


    reply = "HTTP/1.0 200 Connection established\r\n"
    reply += "Proxy-agent: proxy.py\r\n"
    reply += "\r\n"
    client.sendall(reply.encode())
    client.setblocking(0)
    proxy.setblocking(0)

    while True:
        try:
            request = client.recv(8192)
            proxy.sendall(request)
            
        except Exception as err:
            pass
        try:
            reply = proxy.recv(8192)

            client.sendall(reply)
        except Exception as e:
            pass    
    proxy.close()

    client.close()
    

def assign(client,address):
    request = client.recv(4096)
    request = request.decode("utf-8")
    print(request)
    server_address= parse_http(request)
    if server_address == 1:
        handle_https(client,address,request)

    else:
        server_ip = get_ip(server_address)
        data = get_data(server_ip,client,address,request,server_address)

if __name__ == "__main__" :

    admin_panel()

    ip = "127.0.0.1"
    port = 6789
    
    proxy = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    proxy.bind((ip,port))
    proxy.listen(10)

    print('Listening on port 6789....\n')

    while True:
        
        client,address = proxy.accept()
        start_new_thread(assign,(client,address))
            
        signal.signal(signal.SIGINT, signal_handler)