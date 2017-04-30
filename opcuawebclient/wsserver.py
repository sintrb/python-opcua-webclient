# -*- coding: UTF-8 -*
#!/usr/bin/env python

'''
Created on 2017年2月18日

@author: RobinTang
'''


import logging
import tornado.websocket
import threading
import json
logger = logging.getLogger('tornado.ws')
class ChannelSocketHandler(tornado.websocket.WebSocketHandler):
    channelmap = {
                  }
    channellock = threading.Lock()
    channel = None
    errorcount = 0
    def check_origin(self, origin):  
        return True
    
    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}
    
    @classmethod
    def add_connect(cls, con):
        ch = con.channel
        logger.info("add connect %r", con)
        with cls.channellock:
            if ch not in cls.channelmap:
                cls.channelmap[ch] = {
                   'clients':[],
                   'name':ch,
                   'count':0,
                   'tagmap':{}
                }
            cls.channelmap[ch]['clients'].append(con)
            cls.channelmap[ch]['count'] = len(cls.channelmap[ch]['clients'])

    @classmethod
    def del_connect(cls, con):
        logger.info("del connect %r", con)
        ch = con.channel
        with cls.channellock:
            if ch in cls.channelmap:
                cls.channelmap[ch]['clients'].remove(con)
                ntagmp = {}
                for k, v in cls.channelmap[ch]['tagmap'].items():
                    if con in v:
                        v.remove(con)
                    if v:
                        ntagmp[k] = v
                cls.channelmap[ch]['tagmap'] = ntagmp
                cls.channelmap[ch]['count'] = len(cls.channelmap[ch]['clients'])
                if not cls.channelmap[ch]['clients']:
                    del cls.channelmap[ch]
    
    @classmethod
    def add_subscribe(cls, con, tag):
        logger.info("add subscribe %r %s", con, tag)
        ch = con.channel
        with cls.channellock:
            tagmap = cls.channelmap[ch]['tagmap']
            if tag not in tagmap:
                tagmap[tag] = []
            if con not in tagmap[tag]:
                tagmap[tag].append(con)
        return con
    
    @classmethod
    def send_message_to_con(cls, con, message):
        try:
            logger.debug("send message to con %s:%s", con, message)
            con.write_message(message if isinstance(message, basestring) else json.dumps(message))
            con.errorcount = 0
            return True
        except:
            con.errorcount += 1
            return False
    
    @classmethod
    def send_message(cls, channel, message, tag=None, igncons=None):
        logger.debug("send message to %s[%s]:%s", channel, tag, message)
        if channel not in cls.channelmap:
            return 0
        count = 0
        dieclients = []
        tagmap = cls.channelmap[channel]['tagmap']
        messagejson = json.dumps(message)
        if tag in tagmap:
            for con in tagmap[tag]:
                if con == igncons:
                    continue
                if ChannelSocketHandler.send_message_to_con(con, messagejson):
                    count += 1
                if con.errorcount >= 3:
                    dieclients.append(con)
            map(cls.del_connect, dieclients)
        return count
    
    @classmethod
    def send_data(cls, channel, data, tag=None, igncons=None):
        logger.debug("send to %s[%s]:%s", channel, tag, data)
        return ChannelSocketHandler.send_message(channel, {
                                                  'type':'data',
                                                  'tag':tag,
                                                  'data':data
                                                  }, tag, igncons)
    
    def open(self, channel):
        if not channel:
            self.close()
            return
        self.channel = channel
        logger.info("open %r", self)
        ChannelSocketHandler.add_connect(self)


    def on_close(self):
        logger.info("close %r", self)
        ChannelSocketHandler.del_connect(self)

    def on_message(self, data):
        logger.info("got data %r", data)
        data = json.loads(data)
        msgtype = data.get('type')
        if msgtype == 'subscribe':
            # 订阅
            tag = data.get('tag')
            cid = str(id(ChannelSocketHandler.add_subscribe(self, tag)))
            return ChannelSocketHandler.send_message_to_con(self, {
                                                      'type':'subscribe',
                                                      'data':{
                                                              'cid':cid
                                                              }
                                                      })
        elif msgtype == 'data':
            # 数据
            tag = data.get('tag')
            # 暂不处理上行数据
            ChannelSocketHandler.send_data(self.channel, data.get('data'), tag, igncons=self)
    
    def __repr__(self, *args, **kwargs):
        return '%s @%s' % (self.request.remote_ip, self.channel)

