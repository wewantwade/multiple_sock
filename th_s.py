import os
import pickle
import socket
import threading
from tkinter import *
from tkinter.ttk import *
import struct#二进制转换模块

#定义一个默认备份目录
BAK_PATH='/home/ubuntu/hh/'
SERV_RUN_FLAG=True
# flag_lock=threading.Lock()

def client_operate(client):
    # 接收发送方的文件信息，包括各个文件的大小和路径
    files_lst = get_files_info(client)  # 定义一个方法get_files获取客户端发送的文件信息列表
    for size, filepath in files_lst:  # 遍历列表中的文件大小和路径
        res = recv_file(client, size, filepath)  # 定义recv_file函数备份文件（大小，路径）
        send_echo(client, res)  # 备份完成一个文件，就发送一次成功备份的信息
    # 备份完成关闭套接字和客户端链接
    client.close()
#启动服务器
def start(host,port):
    print('the addr:', host + ":" + str(port))
    print('wait client connect....')
    if not os.path.exists(BAK_PATH):
        os.mkdir(BAK_PATH)
    st=socket.socket()
    #st.settimeout(1)#为服务器设置超时选项，服务器启动后，如果在一秒之内客户端还没有连接上，则进入下一个循环
    st.bind((host,port))
    st.listen(1)
    # flag_lock.acquire()#获得锁，对SERV_RUN_FLAG的访问权
    while SERV_RUN_FLAG:
        # flag_lock.release()
        client=None
        try:
            client,addr=st.accept()
            print('already connected:',addr)
        except socket.timeout:
            pass
        if client:
            t=threading.Thread(target=client_operate,args=(client,))
            t.start()
        # flag_lock.acquire()
    st.close()

#接收文件信息，返回文件数据
def recv_unit_data(clnt,infos_len):
    data=b''
    #如果文件信息长度小于1024，一次性进行接收，如果大于1024，则分多次进行接收信息
    if 0<infos_len<=1024:
        data+=clnt.recv(infos_len)
    else:
        while True:
            if infos_len>1024:
                data+=clnt.recv(1024)
                infos_len-=1024
            else:
                data+=clnt.recv(infos_len)
                break
    return data


#获取文件信息
def get_files_info(clnt):
    #定义一个格式串，代表向服务器端发送文件信息的大小Q，长整数
    fmt_str='Q'
    #计算出fmt_str长整形数的大小
    headsize=struct.calcsize(fmt_str)
    #根据计算结果接受此信息
    data=clnt.recv(headsize)
    #将接收到的信息解开，获取文件信息大小
    infos_len=struct.unpack(fmt_str,data)[0]
    #根据文件信息大小接收文件信息
    data=recv_unit_data(clnt,infos_len)
    return pickle.loads(data)#客户端发送的文件信息是经过pickle二进制编码的，此时需要解开获取到文件的大小和路径列表

#建立文件路径函数（当客户端发送的文件路径在默认备份路径下不存在时，要建立这个文件路径）
def mk_path(filepath):
    paths=filepath.split(os.path.sep)[:-1]#将文件名进行分割并去掉文件名
    p=BAK_PATH
    for path in paths:
        # 遍历客户端传来的路径，将这些路径逐一添加到默认路径上面
        p=os.path.join(p,path)
        if not os.path.exists(p):
            os.mkdir(p)

#备份文件的主方法
def recv_file(clnt,infos_len,filepath):
    #首先根据客户端发送的文件路径对路径进行建立
    mk_path(filepath)
    #建立服务器上的文件路径，包括文件名
    filepath=os.path.join(BAK_PATH,filepath)
    #打开建立好的文件，写入数据
    f=open(filepath,'wb+')
    try:
        if 0<infos_len<1024:
            data=clnt.recv(infos_len)
            f.write(data)
        else:
            while True:
                if infos_len>1024:
                    data=clnt.recv(1024)
                    f.write(data)
                    infos_len-=1024
                else:
                    data=clnt.recv(infos_len)
                    f.write(data)
                    break
    except:
        print('error')
    else:
        return True
    finally:
        f.close()

#向客户端发送是否备份成功的消息
def send_echo(clnt,res):
    if res:
        clnt.sendall(b'success')
    else:
        clnt.sendall(b'failure')
#定义一个类继承frame
class MyFrame(Frame):
    #定义初始化方法
    def __init__(self,root):
        super().__init__(root)
        self.root=root
        self.grid()#网格布局
        self.local_ip=['127.0.0.1']
        self.serv_ports=[10888,20888,30888]#服务器端口
        self.init_components()#定义一个界面的初始化方法

    #界面初始化方法
    def init_components(self):
        #窗口名称
        project_name=Label(self,text="远程备份服务器")
        project_name.grid(columnspan=2)
        #IP标签
        serv_ip_label=Label(self,text="服务地址:")
        serv_ip_label.grid(row=1)
        #IP输入框
        self.serv_ip=Combobox(self,values=self.get_ipaddr())
        self.serv_ip.set(self.local_ip)
        self.serv_ip.grid(row=1,column=1)
        #端口标签
        serv_port_label=Label(self,text="服务端口")
        serv_port_label.grid(row=2)
        #端口输入框
        self.serv_port=Combobox(self,values=self.serv_ports)
        self.serv_port.set(self.serv_ports[0])
        self.serv_port.grid(row=2,column=1)
        #启动服务和关闭服务的端口
        self.start_serv_btn=Button(self,text="启动服务",command=self.start_serv)
        self.start_serv_btn.grid(row=3)
        self.start_exit_btn=Button(self,text="退出服务",command=self.root.destroy)
        self.start_exit_btn.grid(row=3,column=1)

    #获取主机IP地址方法
    def get_ipaddr(self):
        host_name=socket.gethostname()
        print('hostname是:',host_name)
        info=socket.gethostbyname_ex(host_name)#到到主机的相关信息
        info=info[2]
        info.append(self.local_ip)
        return info
def start_serv():
        host='0.0.0.0'
        port=int(8881)
        serv_th=threading.Thread(target=start,args=(host,port))
        serv_th.start()
        # self.start_serv_btn.state(['disabled',])
        # print(self.serv_ip.get(),self.serv_port.get())
        # start(self.serv_ip.get(),int(self.serv_port.get()))

# class MyTk(Tk):
#     def destroy(self):
#         global SERV_RUN_FLAG
#         while True:
#             if flag_lock.acquire():
#                 SERV_RUN_FLAG=False
#                 flag_lock.release()
#                 break
#         super().destroy()

if __name__=='__main__':
    # root=MyTk()
    # root.title('备份服务器')
    # # root.geometry('200x100')
    # root.resizable(True,True)#设置大小不可变
    # app=MyFrame(root)
    # app.mainloop()
    start_serv()
