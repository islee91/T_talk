from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *

import socket
import threading
from threading import Thread

lock=threading.Lock()
#lock.acquire()
#--------
#lock.release()


host='localhost'
port=14444


sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#------------------------------------------------------------
def startset():
    
    userlist.delete(0,END)
    
    ip_entry.config(state='normal')
    ip_entry.delete(0,END)
    ip_entry.insert(0,host)

    port_entry.config(state='normal')
    port_entry.delete(0,END)
    port_entry.insert(0,port)

    ID_entry.config(state='normal')
    ID_entry.delete(0,END)
    
    PW_entry.config(state='normal')
    PW_entry.delete(0,END)
    
    chatbox.config(state='normal')
    chatbox.delete(1.0,END)
    chatbox.config(state='disabled')

    sendbutton.config(state='disabled')
    msgEntry.delete(0,END)
    msgEntry.config(state='disabled')


ID_flag=0
def ID_command():
    global sock
    
    if ID_flag==0:    #계정생성
        try:
            sock.connect( ( str(ip_entry.get()),int(port_entry.get()) ) )
        except:
            messagebox.showinfo(title='접속실패', message='서버와 연결 불가능.\nip,port를 확인하십시오.')
            sock.close()
            return
        sock.send(  ( '0000000030'+ID_entry.get()+':'+PW_entry.get() ).encode()  )
        msg=sock.recv(1024)
        sock.close()
        if msg.decode()[10]=='y':    #계정생성 성공
            messagebox.showinfo(title='성공', message='계정이 생성되었습니다.')
        elif msg.decode()[10]=='n':    #계정생성 실패
            messagebox.showinfo(title='실패', message='계정 생성 실패.')
        else:
            messagebox.showinfo(title='오류', message='잘못된 신호 받음. 오류.')
        return


    else:    #계정삭제신청.
        if PW_entry.get()=='':
            messagebox.showinfo(title='계정삭제', message='비밀번호를 입력해주세요.')
            return
        sock.send(  ( '0000000040'+ID_entry.get()+':'+PW_entry.get() ).encode()  )
        


login_flag=0
def login_command():
    global login_flag,ID_flag,sock
    
    if login_flag==0:    #로그인
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect( ( str(ip_entry.get()),int(port_entry.get()) ) )
        except:
            messagebox.showinfo(title='접속실패', message='서버와 연결 불가능.\nip,port를 확인하십시오.')
            sock.close()
            return
        sock.send(  ( '0000000010'+ID_entry.get()+':'+PW_entry.get() ).encode()  )
        msg=sock.recv(1024)
        if msg.decode()[10]=='y':    #로그인성공
            rcvmsgth=Thread(target=rcvMsg, args=(sock,))
            rcvmsgth.daemon=True
            rcvmsgth.start()
            ip_entry.config(state='disabled')
            port_entry.config(state='disabled')
            ID_entry.config(state='disabled')
            PW_entry.config(state='disabled')
            login_flag=1
            ID_flag=1
            ID_button.config(text='계정삭제')
            login_button.config(text='로그아웃')
            sendbutton.config(state='normal')
            msgEntry.config(state='normal')
            userlist.insert(END,ID_entry.get())
            return
        elif msg.decode()[10]=='n':
            messagebox.showinfo(title='실패', message=msg.decode()[12:])
        else:
            messagebox.showinfo(title='오류', message='잘못된 신호 받음. 오류.')
        sock.close()
        return


    else:    #로그아웃
        sock.send( ( '0000000020'+ID_entry.get() ).encode() )
        login_flag=0
        ID_flag=0
        ID_button.config(text='계정생성')
        login_button.config(text='로그인')
        startset()
        sock.close()
        return



def send_msg():
    sock.send( ( '0000000001'+ID_entry.get()+':'+msgEntry.get() ).encode() )
    msgEntry.delete(0,END)
    
def enterpress(n):
    if msgEntry.get()!='':
        send_msg()

    


def rcvMsg(sock):
    global ID_flag,login_flag
    
    while True:
        try:
            data = (sock.recv(1024)).decode()
            print('d: '+data)
            if data=='':
                break
        except:
            break
        try:
            if data[9]=='1':    #메시지
                data=data[10:].split(':')
                chatbox.config(state='normal')
                chatbox.insert(END,data[0]+' : '+data[1]+'\n')
                chatbox.config(state='disabled')
            
            elif data[7]=='1':    #갱신
                data=data[10:].split(':')
                if data[1]==' ':    #로그인갱신
                    x=data[0].split(',')
                    for i in x:
                        userlist.insert(END,i)
                elif data[1]=='':    #추가
                    userlist.insert(END,data[0])
                else:    #제거
                    i=userlist.get(0,END).index(data[1])
                    userlist.delete(i)
                    
            elif data[8]=='4':    #계정삭제결과
                if data[10]=='n':
                    messagebox.showinfo(title='계정삭제', message='계정삭제 실패.')
                elif data[10]=='y':
                    login_flag=0
                    ID_flag=0
                    ID_button.config(text='계정생성')
                    login_button.config(text='로그인')
                    startset()
                    sock.close()
                else:
                    messagebox.showinfo(title='계정삭제', message='오류')
                    
            else:
                pass#무시
        except:
            pass




#------------------------------------------------------------
#Gui 구성.

win=Tk()
win.title('T-talk 클라이언트')
win.geometry('600x400+100+100')
win.resizable(0,0)

win.bind('<Control-s>',enterpress)

#------------------------------------------------------------
#------------------------------------------------------------
#1구역

ip_label=Label(win,text='ip:')
ip_label.place(x=450,y=5)
ip_entry=Entry(win,width=15)
ip_entry.place(x=480,y=5)

port_label=Label(win,text='port:')
port_label.place(x=450,y=28)
port_entry=Entry(win,width=15)
port_entry.place(x=480,y=28)

ID_label=Label(win,text='ID:')
ID_label.place(x=450,y=51)
ID_entry=Entry(win,width=15)
ID_entry.place(x=480,y=51)

PW_label=Label(win,text='PW:')
PW_label.place(x=450,y=74)
PW_entry=Entry(win,width=15,show='*')
PW_entry.place(x=480,y=74)

ID_button=Button(win,text='계정생성',width=8,command=ID_command)
ID_button.place(x=450,y=97)

login_button=Button(win,text='로그인',width=8,command=login_command)
login_button.place(x=526,y=97)

userframe=Frame(win)
userframe.place(x=450,y=133)
userscroll=Scrollbar(userframe)
userscroll.pack(side='right',fill='y')
userlist=Listbox(userframe,yscrollcommand=userscroll.set,width=17,height=14)
userlist.pack(side='left')
userscroll.config(command=userlist.yview)


#------------------------------------------------------------
#------------------------------------------------------------
#2구역

chatframe=Frame(win)
chatframe.place(x=5,y=5)
chatscroll=Scrollbar(chatframe)
chatscroll.pack(side='right',fill='y')
chatbox=Text(chatframe,width=60,height=27,yscrollcommand=chatscroll.set)
chatbox.pack(side='left')
chatscroll.config(command=chatbox.yview)

msgEntry=Entry(win,width=66)
msgEntry.place(x=5,y=370)

sendbutton=Button(win,text='보내기(Ctrl+s)',width=14,command=send_msg)
sendbutton.place(x=480,y=368)


#------------------------------------------------------------
#------------------------------------------------------------

startset()

win.mainloop()
sock.close()


