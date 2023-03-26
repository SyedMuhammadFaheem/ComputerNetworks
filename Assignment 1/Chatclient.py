import socket
import threading
from tkinter import *
client=None
def press(event):
    sendMsg()

def establishConnection():
    global client
    client= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    if portField.get()!='':
        try:
            ip,port=portField.get().split(' ')
            client.connect((ip,int(port)))
        except:
            establishConnection()
    portField.delete(0,END)
    connLabel.config(text='Connection Status: Connected Successfully!')
    threading.Thread(target=recvMsg).start()

def recvMsg():
    global client
    while True:
        recieved=client.recv(1024).decode('utf-8')
        if recieved=='quit':
            client.close()
            root.destroy()
            root.quit()
            root.destroy()
            break
        else:
            txt.insert(END,'Recieved: '+ recieved+'\n')        

def sendMsg():
    global client
    if msgField.get()!='':
        client.send(msgField.get().encode('utf-8'))
        txt.insert(END,'Sent: '+ msgField.get()+'\n') 
        if msgField.get()=='quit':
            client.close()
            root.destroy()
            root.quit()
            root.destroy()
        msgField.delete(0,END)


root = Tk()
root.geometry('895x300')
root.title('Client Interface')
root.title('Server Interface')
root.config(bg='black')
root.resizable(0, 0)
frame=Frame(root)
frame.place(x=20,y=80)
verticalScroll=Scrollbar(frame)
verticalScroll.pack(side=RIGHT,fill=Y)
txt=Text(frame,width=90,height=10,yscrollcommand = verticalScroll.set,bg='black',fg='white')
txt.pack(side=TOP, fill=X)
verticalScroll.config(command=txt.yview)
portLabel = Label(root, text='Enter IP and Port: ',
                   font=('arial', 14, 'bold'), bg='black',fg='white')
portLabel.place(x=20, y=15)
portField = Entry(root, width=50, font=(
    'arial', 14, 'bold'))
portField.place(x=195, y=15)
listenBtn = Button(root, text="Start Listening", bd=0, bg='white',fg='black',
                       relief=RAISED, command=establishConnection).place(x=770, y=15)
connLabel = Label(root, text='Connection Status: Not Connected!',
                   font=('arial', 14, 'bold'),bg='black',fg='white')
connLabel.place(x=20, y=50)
msgField = Entry(root, width=66, font=(
    'arial', 14, 'bold'))
msgField.place(x=20, y=250)
msgField.bind("<KeyRelease-Return>", press)
sendBtn = Button(root, text="Send Message", bd=0, bg='white',fg='black',
                       relief=RAISED, command=sendMsg).place(x=775, y=250)
root.mainloop()
