#coding=utf8
import requests
import re
import base64
import json
import binascii
import rsa
import os
import time
from PIL import Image

class Weibo():
    def __init__(self, username, password):
        self.session = requests.session()
        self.username = username
        self.password = password
        self.uid = ""
        self.code = ""
        self.pcid = ""

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
        if self.code != "" and self.pcid != "":
            postdata['pcid'] = self.pcid
            postdata['door'] = self.code
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

    def checkCode(self):
        su = base64.b64encode(self.username.encode(encoding="utf-8")) #将用户名编码
        url = "https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.19)&_=1548056423021" % su.decode("utf-8")
        respo = self.session.get(url)
        showpin = re.findall(r'showpin":([0|1])', respo.text)
        #判断showpin值是否存在
        if len(showpin)==1:
            pcid_re = re.findall(r'"pcid":"(.+?)"', respo.text)
            return pcid_re[0] #返回需要验证码时的p值
        else:
            return False #无需验证码

    def getCodeImg(self,pcid):
        url = "https://login.sina.com.cn/cgi/pin.php?r=35784298&s=0&p=%s" % pcid
        codeimg = self.session.get(url).content
        self.pcid = pcid
        return codeimg

    def setCode(self,code):
        self.code = code

    def sendWeibo(self,text):
        self.Header = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "177",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "weibo.com",
            "Origin": "http://weibo.com",
            "Referer": "http://weibo.com/u/" + self.uid + "/home?wvr=5&c=spr_qdhz_bd_360jsllqcj_weibo_001",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"}
        sendurl="https://weibo.com/aj/mblog/add?ajwvr=6&__rnd=1504967427943"
        formdata={"location": "v6_content_home",
                "text": text,
                "style_type": "1",
                "rank": "0",
                "isReEdit": "false",
                "module": "stissue",
                "pub_source": "main_",
                "pub_type": "dialog",
                "isPri":"0",
                "_t": "0"}
        return_text = self.session.post(sendurl, data=formdata,headers=self.Header).text
        data = json.loads(return_text)
        if data['code'] == "100000":
            print("发表成功")
        else:
            print("发表失败")

    def getUrl(self):
        self.session.get("http://weibo.com/u/" + self.uid)

if __name__ == "__main__":
    username = input("请输入账号：")
    password = input("请输入密码：")
    weibo = Weibo(username, password)
    pcid = weibo.checkCode()
    if pcid != False:
        with open("code.png", "wb") as file:
            file.write(weibo.getCodeImg(pcid))
        Image.open("code.png").show()
        code = input("请输入验证码：")
        weibo.setCode(code)
    weibo.userLogin()
    bday = input("请输入生日,格式:01-31：")
    jlday = ""
    while True:
        today =  time.strftime('%m-%d', time.localtime(time.time()))
        if today!=jlday:
            print(jlday, today, bday)
            if today==bday:
                weibo.sendWeibo("生日快乐![蛋糕]")
            else:
                weibo.sendWeibo("不是今天![微风]")
            jlday = today
        time.sleep(300)
        weibo.getUrl()