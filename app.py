#coding=utf8
import requests
import re
import base64
import json
import binascii
import rsa
import os
class Weibo():
    def __init__(self, username, password):
        self.session = requests.session()
        self.username = username
        self.password = password
        self.uid = ""

    def userLogin(self, pagecount=1):
        #登录微博
        get_Header = {"User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"}
        #添加请求头信息
        url_prelogin = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=&rsakt=mod&client='
        url_login = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.5)'
        resp = self.session.get(url_prelogin, headers=get_Header)
        #模拟请求需要获取到加密的公钥
        json_data = re.findall(r'(?<=\().*(?=\))', resp.text)[0]
        data = json.loads(json_data)
        #取出json数据
        servertime = data['servertime']
        nonce = data['nonce']
        pubkey = data['pubkey']
        rsakv = data['rsakv']
        #取出需要用到的参数和公钥
        su = base64.b64encode(self.username.encode(encoding="utf-8"))
        #bs64加密账号
        rsapublickey = int(pubkey, 16)
        #转换进制
        key = rsa.PublicKey(rsapublickey,65537)
        #设置公钥
        message = str(servertime)+'\t'+str(nonce)+'\n'+str(self.password)
        #加密的密码明文文本
        sp = binascii.b2a_hex(rsa.encrypt(message.encode(encoding="utf-8"), key))
        #进行rsa加密以及进制转换
        postdata = {
            'entry':'weibo',
            'gateway':'1',
            'from':'',
            'savestate':'7',
            'userticket':'1',
            'ssosimplelogin':'1',
            'vsnf':'1',
            'vsnval':'',
            'su':su,
            'service':'miniblog',
            'servertime':servertime,
            'nonce':nonce,
            'pwencode':'rsa2',
            'sp':sp,
            'encoding':'UTF-8',
            'url':'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype':'META',
            'rsakv':rsakv,
            }
        resp=self.session.post(url_login,data=postdata,headers=get_Header)
        #发送请求
        login_url=re.findall(r'http://weibo.*&retcode=0', resp.text)
        #取出跳转链接
        try:
            respo = self.session.get(login_url[0], headers=get_Header)
            uid = re.findall('"uniqueid":"(\d+)",', respo.text)[0]
            #登录获取已登录的Uid账号
            self.uid = uid
            url = "http://weibo.com/u/" + uid
            respo = self.session.get(url, headers=get_Header).text
            print("登录成功 uid:%s" %uid)
        except IndexError:
            print("登录失败")
            os._exit(0)


if __name__ == "__main__":
    username = input("请输入账号：")
    password = input("请输入密码：")
    weibo = Weibo(username, password)
    weibo.userLogin()