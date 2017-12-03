



import os
import pickle
import socket
import threading
from tkinter import *
from tkinter.ttk import *
import struct#二进制转换模块


#获取要备份的所有文件的信息
def get_file_info(path):
    if not path or not os.path.exists(path):
        return None
    files=os.walk(path)#os模块中的walk方法获取路径中的所有文件
    print('文件:',files)
    #定义文件信息列表和文件路径的列表
    infos=[]
    file_paths=[]
    #p是指当前文件的文件路径，ds是指当前文件夹内的所有文件夹，fs是指当前文件夹内的所有文件
    for p,ds,fs in files:
        # print('p:',p)
        # print('ds:', ds)
        # print('fs:',fs)
        for f in fs:
            file_name=os.path.join(p,f)#获取文件名并添加到当前路径下
            file_size=os.stat(file_name).st_size#获取当前文件的大小
            file_paths.append(file_name)
            print('file_paths:',file_paths)
            file_name=file_name[len(path)+1:]
            print('file_name:',file_name)
            infos.append((file_size,file_name))
            print('infos:',infos)
    return infos,file_paths

#向服务器端发送文件信息
def send_files_infos(my_sock,infos):
    fmt_str='Q'
    #对所有的文件信息进行二进制编码
    infos_bytes=pickle.dumps(infos)
    #获取二进制编码后的文件信息的长度
    infos_bytes_len=len(infos_bytes)
    #将长度也进行二进制编码
    infos_len_pack=struct.pack(fmt_str,infos_bytes_len)
    my_sock.sendall(infos_len_pack)
    my_sock.sendall(infos_bytes)


#向服务器发送所有文件
def send_files(my_sock,file_path):
    f=open(file_path,'rb')
    try:
        while True:
            data=f.read(1024)
            if data:
                my_sock.sendall(data)
            else:
                break
    finally:
        f.close()

#接收反馈信息
def get_bak_info(my_sock,size=7):
    info=my_sock.recv(size)
    print(info.decode('utf-8'))

#启动服务器
def start(host,port,src):
    if not os.path.exists(src):
        print('备份的目标不存在')
        return
    s=socket.socket()
    s.connect((host,port))
    path=src
    #获取每一个文件信息和路径
    file_infos,file_paths=get_file_info(path)
    ##发送文件信息
    send_files_infos(s,file_infos)
    for fp in file_paths:

         #发送文件列表中的每一个文件
        send_files(s,fp)
        print(fp)
         #获取备份结果是否成功
        get_bak_info(s)
    s.close()

#定义一个类继承frame
class MyFrame(Frame):
    #定义初始化方法
    def __init__(self,root):
        super().__init__(root)
        self.root=root
        self.grid()#网格布局
        #定义要连接的服务器IP和端口
        self.remote_ip='47.95.115.79'
        self.remote_port=8881
        #用户要连接的ip输入框,端口输入框，备份文件的输入框
        self.remote_ip_var=StringVar()
        self.remote_ports_var=IntVar()
        self.bak_src_var=StringVar()
        self.init_components()#定义一个界面的初始化方法

    #界面初始化方法
    def init_components(self):
        #窗口名称
        project_name=Label(self,text="远程备份客户机")
        project_name.grid(columnspan=2)
        #IP标签
        serv_ip_label=Label(self,text="服务地址:")
        serv_ip_label.grid(row=1)
        #IP输入框
        self.serv_ip=Entry(self,textvariable=self.remote_ip_var)
        self.remote_ip_var.set(self.remote_ip)
        self.serv_ip.grid(row=1,column=1)
        #端口标签
        serv_port_label=Label(self,text="服务端口:")
        serv_port_label.grid(row=2)
        #端口输入框
        self.serv_port=Entry(self,textvariable=self.remote_ports_var)
        self.remote_ports_var.set(self.remote_port)
        self.serv_port.grid(row=2,column=1)
        #用户的备份文件目录
        src_lable=Label(self,text="备份的目标:")
        src_lable.grid(row=3)

        self.bak_src=Entry(self,textvariable=self.bak_src_var)
        self.bak_src.grid(row=3,column=1)
        #启动服务和关闭服务的端口
        self.start_serv_btn=Button(self,text="开始备份",command=self.start_send)
        self.start_serv_btn.grid(row=4)
        self.start_exit_btn=Button(self,text="退出服务",command=self.root.destroy)
        self.start_exit_btn.grid(row=4,column=1)

    def start_send(self):
        # print(self.remote_ip_var.get(),self.remote_ports_var.get())
        # print('start.......')
        # start(self.remote_ip_var.get(),int(self.remote_ports_var.get()),self.bak_src_var.get())
        host=self.remote_ip_var.get()
        port=self.remote_ports_var.get()
        src=self.bak_src_var.get()
        t=threading.Thread(target=start,args=(host,int(port),src))
        t.start()


if __name__=='__main__':
    root=Tk()
    root.title('备份客户机')
    # root.geometry('200x100')
    root.resizable(True,True)#设置大小不可变
    app=MyFrame(root)
    app.mainloop()
