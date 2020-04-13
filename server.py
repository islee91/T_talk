
from os.path import exists
import pickle
import socketserver
import threading
from threading import Thread


# 계정정보 파일:
user_data='server_data01.qwe'


lock=threading.Lock()
#lock.acquire()
#--------
#lock.release()


host=''
port=14444


#아이디 금지어 목록
dontuse=[':',' ',',']


#----------------------------------------------------------------------------------------------------
class Ttalk_system:

    def __init__(self):
        if not exists(user_data):
            print('신규 데이터 파일 생성.')
            self.id_dictionary={'system':['1234',0]}    # 기본으로 system/1234 라는 계정 만든다.
            userdatafile=open(user_data,'wb')
            pickle.dump(self.id_dictionary,userdatafile)
            userdatafile.close()
            
        self.login_list={}
        userdatafile=open(user_data,'rb')
        self.id_dictionary=pickle.load(userdatafile)    # id_dictionary 는 들고있는다.
        userdatafile.close()
        print('데이터 파일 읽기 완료.')

    def create_ID(self,id,pw):
        if id in self.id_dictionary:
            return 1    #중복아이디의 경우.
        for i in dontuse:
            if i in id or i in pw:
                return 2    #아이디,패스워드에 금지어 있음.
        if len(id)<4 or len(id)>10 or len(pw)<4 or len(pw)>10:
            return 3    #아이디, 패스워드 길이제한 위반.
        self.id_dictionary[id]=[pw,0]
        userdatafile=open(user_data,'wb')
        pickle.dump(self.id_dictionary,userdatafile)
        userdatafile.close()
        return 0    #아이디 생성 성공.

    def delete_id(self,id,pw,admin=0):
        if id in self.id_dictionary:
            if admin==0:
                if self.id_dictionary[id][0]!=pw:
                    return 1    #비밀번호가 틀렸음.
            del self.id_dictionary[id]
            userdatafile=open(user_data,'wb')
            pickle.dump(self.id_dictionary,userdatafile)
            userdatafile.close()
            return 0    #아이디 삭제 성공.
        return 2    #아이디 존재 안함.

    def log_in(self,id,pw,conn,addr):
        if id not in self.id_dictionary:
            conn.send(  '0000000010n:존재하지 않는 아이디.'.encode()  )
            return 1    #존재하지 않는 아이디.
        if id in self.login_list:
            conn.send(  '0000000010n:이미 로그인 된 아이디.'.encode()  )
            return 2    #이미 로그인 된 아이디.
        if self.id_dictionary[id][0]==pw:
            self.send_msg_all('0000000100'+id+':')    #접속자들에게 갱신.
            conn.send('0000000010y:성공'.encode())
            x=''
            n=0
            for i in self.login_list:    #접속목록 보내주기. (본인은 제외하고 보내줌.)
                x+=i+','
                n+=1
                if n==30:
                    n=0
                    x=x[:-1]
                    conn.send( ('0000000100'+x+': ').encode() )
                    x=''
            if n>0:
                x=x[:-1]
                conn.send( ('0000000100'+x+': ').encode() )
            self.login_list[id]=[conn,addr]
            return 0    #로그인 성공.
        conn.send(  '0000000010n:비밀번호가 틀렸습니다.'.encode()  )
        return 3    #비밀번호 오류.

    def log_out(self,id):
        if id not in self.login_list:
            return 1    #로그인된 아이디가 아님.
        del self.login_list[id]
        self.send_msg_all('0000000100:'+id)    #접속자들에게 갱신.
        return 0
    
    def send_msg_1(self,recv,msg):    #특정 유저에게 메시지 보내기. (여기선 이거 쓸일 없을거같은데....)
        if recv in self.login_list:
            self.login_list[recv][0].send(msg.encode())
            return 0
        return 1    #존재하지 않는 유저.

    def send_msg_all(self,msg):    #접속자 모두에게 메시지 보내기.
        for i in self.login_list:
            self.login_list[i][0].send(msg.encode())
        return





Ts=Ttalk_system()
#----------------------------------------------------------------------------------------------------
class ChatHandler(socketserver.BaseRequestHandler):

    def handle(self):
        msg=self.request.recv(1024)
        msg=msg.decode()

        if msg[8]=='1':    #로그인
            msg=msg[10:]
            msg=msg.split(':')
            name=msg[0]
            lock.acquire()
            if Ts.log_in(msg[0],msg[1],self.request,self.client_address)>0:    #로그인은 결과 알아서 다 보내줌.
                lock.release()
                self.request.close()
                return
            lock.release()
            
        elif msg[8]=='3':    #계정생성
            msg=msg[10:]
            msg=msg.split(':')
            lock.acquire()
            if Ts.create_ID(msg[0],msg[1])==0:    #성공
                self.request.send('0000000030y:성공'.encode())
            else:    #실패
                self.request.send('0000000030n:실패'.encode())
            lock.release()
            self.request.close()
            return
        
        else:    #오류. 끝.
            self.request.close()
            return
        

        while 1:    #로그인 성공한 상태.
            try:
                msg=self.request.recv(1024)
            except Exception as e:   #강제섭종의 경우.
                print(e)
                break
            msg=msg.decode()

            if msg[9]=='1':    #대화메시지
                lock.acquire()
                Ts.send_msg_all(msg)
                lock.release()

            elif msg[8]=='2':    #로그아웃
                break

            elif msg[8]=='4':    #계정삭제
                msg=msg[10:]
                msg=msg.split(':')
                lock.acquire()
                if Ts.delete_id(msg[0],msg[1])==0:
                    lock.release()
                    self.request.send('0000000040y:성공'.encode())
                    break
                else:
                    lock.release()
                    self.request.send('0000000040n:실패'.encode())

            else:    #오류. 무시.
                pass
                
        lock.acquire()
        Ts.log_out(name)    #로그아웃.
        lock.release()
        self.request.close()





#-----------------------------------------------------------------
class ChatServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

def ServerStart(h,p):
    print('## T-talk 서버 가동 시작.')
    print('## host: '+str(h)+', port: '+str(p))
    try:
        server=ChatServer( (h,p), ChatHandler )
        server.serve_forever()
    except:
        server.shutdown()
        server.server_close()

ss=Thread(target=ServerStart, args=(host,port,))
ss.daemon=True
ss.start()


while 1:
    com=input('\n명령:')
    if com=='?':
        print('접속자목록 보기: loginlist')
        print('계정목록 보기: idlist')
        print('특정 id 삭제: del id')
    elif com=='loginlist':    #접속자목록보기
        print(Ts.login_list)
    elif com=='idlist':    #계정목록보기.
        print(Ts.id_dictionary)
    elif 'del' in com:
        com=com.split(' ')
        x=Ts.delete_id(com[1],0,admin=1)
        if x==0:
            print(com[1]+' 계정 삭제 성공.')
        else:
            print('계정삭제 오류.')
    else:
        print("'?'를 입력하세요.")

    





