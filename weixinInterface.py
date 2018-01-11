#fuliali
# -*- coding: utf-8 -*-
import hashlib
import web
import lxml
import time
import os
import re
import json
import urllib,urllib2
from lxml import etree
import requests

class WeixinInterface:

    def __init__(self):
        self.app_root = os.path.dirname(__file__)
        self.templates_root = os.path.join(self.app_root, 'templates')
        self.render = web.template.render(self.templates_root)

    #函数用来获取用户的ID，发送的消息类型，发送的时间等
    def GET(self):
        data = web.input()
        signature = data.signature
        timestamp = data.timestamp
        nonce = data.nonce
        echostr = data.echostr
        # 自己的token
        token = "自己的token"  # 这里填写在微信公众平台里输入的token
        # 字典序排序
        list = [token, timestamp, nonce]
        list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, list)
        hashcode = sha1.hexdigest()
        # sha1加密算法

        # 如果是来自微信的请求，则回复echostr
        if hashcode == signature:
            return echostr

    def POST(self):
        str_xml = web.data()  # 获得post来的数据
        xml = etree.fromstring(str_xml)  # 进行XML解析
        msgType = xml.find("MsgType").text
        fromUser = xml.find("FromUserName").text
        toUser = xml.find("ToUserName").text

        # 事件：用户关注，自动回复
        if msgType == "event":
            mscontent = xml.find("Event").text
            if mscontent == "subscribe":#订阅就是“subscribe”，如果退订就是“unsubscribe”
                replayText = u'你好，欢迎关注我的微信公众号'
                return self.render.reply_text(fromUser, toUser, int(time.time()), replayText)

        # 用户发送纯文本
        if msgType == 'text':
            content = xml.find("Content").text#获得用户所输入的内容

            #回复音频模板：用户输入关键字“电台”的时候，我们就自动回复心理FM的当天的电台音频
            if content == "电台" or content == "fm" or content == "Fm" or content == "FM":
                url = 'http://m.xinli001.com/fm/'
                #获取网页源码
                fmre = urllib.urlopen(url).read()
                pa1 = re.compile(r'<head>.*?<title>(.*?)-心理FM</title>', re.S)
                #通过正则表达式匹配的当天电台标题
                ts1 = re.findall(pa1, fmre)
                pa3 = re.compile(r'var broadcast_url = "(.*?)", broadcastListUrl = "/fm/items/', re.S)
                #通过正则表达式匹配的当天电台音频的url真址
                ts3 = re.findall(pa3, fmre)

                req = urllib2.Request(ts3[0])
                response = urllib2.urlopen(req)
                redirectUrl = response.geturl()
                musicTitle = ts1[0]
                musicDes = ''
                musicURL = redirectUrl
                HQURL = 'http://m.xinli001.com/fm/'
                return self.render.reply_fm(fromUser, toUser, musicTitle, musicDes, musicURL, HQURL)

            #回复图文模板：
            elif content == u'你好':
                title1 = '你好，元旦快乐！'#标题
                description1 = '给你的祝福。'#摘要描述
                xc = 'http://viewer.maka.im/k/J64391B8'#图片url地址
                pic = 'http://pic33.nipic.com/20130923/11927319_180343313383_2.jpg'#图文的内容url
                return self.render.reply_pic(fromUser, toUser, title1, description1, pic, xc)

            elif content == u'电影':
                douban_url = 'https://movie.douban.com/'
                douban_html = requests.get(douban_url).text
                # . * ? 贪婪 非贪婪模式这五种概念
                # 括号内就是匹配的内容，结果是以列表内含元组的形式。每个元组有四个元素。分别为豆瓣的电影url链接，电影宣传图片，电影标题，电影评分。
                c = re.compile(r' <a onclick="moreurl.*?href="(.*?)"[\s\S]*?src="(.*?)" alt="(.*?)" [\s\S]*?class="subject-rate">(.*?)</span>',re.S)
                DOUBAN = re.findall(c, douban_html)

                # 爬取相应电影的票房
                piaofang_url = 'http://www.cbooo.cn/boxOffice/GetHourBoxOffice?d=%s' % str(time.time()).split('.')[0]
                piaofang_json = requests.get(piaofang_url).text
                PIAOFANG = json.loads(piaofang_json)['data2']

                PIAOFANGS = []
                for piaofang in PIAOFANG:
                    PIAOFANGS.append((piaofang['MovieName'], float(piaofang['sumBoxOffice'])))
                PIAOFANGS = sorted(PIAOFANGS, key=lambda x: x[1], reverse=True)  # 当前票房从大到小排序

                # 多图文的时候，按照票房顺序显示电影的名称，当前票房，电影宣传图片，电影豆瓣URL链接，豆瓣评分这五部分组成
                INFOS = []
                for piao in PIAOFANGS:
                    piaofang_name = piao[0]
                    for douban in DOUBAN:
                        douban = list(douban)
                        ##元组不可修改，将元组转化为列表。
                        douban_name = douban[2]
                        if piaofang_name == douban_name:
                            douban.append(str("%.3f" % (piao[1] / 10000.0)))  # 加入票房，保留三位小数
                            INFOS.append(douban)
                            break
                # 实现多图文的发布
                total_num = len(INFOS)
                if total_num > 10:
                    num = 10
                else:
                    num = total_num
                return self.render.reply_morepic(fromUser, toUser, INFOS, num)

            # 纯文本模板：用户发送纯文本类型消息
            else:
                key = '图灵机器人的key'  ###图灵机器人的key
                api = 'http://www.tuling123.com/openapi/api?key=' + key + '&info='
                info = content.encode('UTF-8')
                url = api + info
                page = urllib.urlopen(url)
                html = page.read()
                dic_json = json.loads(html)
                reply_content = dic_json['text']
                return self.render.reply_text(fromUser, toUser, int(time.time()), reply_content)
