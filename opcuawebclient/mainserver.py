# -*- coding: UTF-8 -*
'''
Created on 2017年4月21日

@author: RobinTang
'''

# -*- coding: UTF-8 -*
'''
Created on 2017年4月1日

@author: RobinTang
'''
from info import __version__
import os, json

import tornado.httpserver
import tornado.ioloop
import tornado.web

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        with open(os.path.join(os.path.dirname(__file__), 'index.html')) as f:
            self.write(f.read())

from opcua import ua, Client

def get_node_value(node):
    try:
        value = str(node.get_value()) or '[empty]'
    except:
        value = "";
    return value

def wrapdata(d):
    return {
        k: v and True
        for k, v in d.items()
        } if d else {}

class ApiHandler(tornado.web.RequestHandler):
    client = Client
    clientdata = {}
    serveruri = None
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
    @classmethod
    def clearOpc(cls):
        try:
            print 'clear opc client'
            ApiHandler.client.disconnect()
            ApiHandler.client = None
            ApiHandler.clientdata = {}
        except:
            pass
        
    def ret(self, data=None, code=0, message=None):
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        if message and code == 0:
            code = -1
        self.write(json.dumps({
            'code':code,
            'msg':message,
            'data':data
        }))
        self.finish()
    def opc_get_node(self, nodeid):
        if not ApiHandler.client:
            raise Exception('Not connected')
        if nodeid:
            node = ApiHandler.client.get_node(str(nodeid))
        else:
            node = ApiHandler.client.get_root_node()
        return node
    def get(self, apiname):
        func = getattr(self, 'api_%s' % apiname, None)
        if not func:
            self.ret(message=u'No such api: %s' % apiname)
        import inspect
        argspec = inspect.getargspec(func)
        funcagrs = argspec.args
        defaults = argspec.defaults
        arginfos = []
        argslen = len(funcagrs) - (len(defaults) if defaults else 0) - 1
        for i, k in enumerate(funcagrs[1:]):
            arg = {
                   'name':k
                   }
            if i >= argslen:
                arg['default'] = defaults[i - argslen] 
            arginfos.append(arg)

        missargs = []
        kvargs = {}
        for p in arginfos:
            name = p['name']
            if not 'default' in p and self.get_argument(name, None) == None:
                missargs.append(name)
            else:
                kvargs[name] = self.get_argument(name, p.get('defualt'))
        if missargs:
            self.ret(message=u'Miss argment(s): %s' % (', '.join(missargs)))
        try:
            res = func(**kvargs)
            self.ret(data=res)
        except:
            import traceback, sys
            traceback.print_exc()
            es = sys.exc_info()
            self.ret(message=es[1].message or str(es[1]) or str(es[0]))
    
    def api_connect(self, serveruri):
        if not ApiHandler.client or ApiHandler.client == Client or ApiHandler.serveruri != serveruri:
            self.api_disconnect()
            try:
                ApiHandler.client = Client(serveruri)
                ApiHandler.client.connect()
                ApiHandler.serveruri = serveruri
            except BaseException, e:
                ApiHandler.client = None
                ApiHandler.serveruri = None
                raise e

    def api_disconnect(self):
        ApiHandler.clearOpc()
    
    def api_get_nodes(self, parentId):
        node = self.opc_get_node(parentId)
        if parentId:
            nodes = node.get_children()
        else:
            nodes = [node]
        return [
                {
                 'NodeId':n.nodeid.to_string(),
                 'DisplayName':n.get_display_name().Text,
                 'BrowseName':n.get_browse_name().to_string(),
                 'value':get_node_value(n),
                 'config':wrapdata(ApiHandler.clientdata.get(n.nodeid.to_string()))
                }
                for n in nodes
            ]

    def api_get_node(self, nodeid):
        node = self.opc_get_node(nodeid)
        return {
                 'NodeId':node.nodeid.to_string(),
                 'DisplayName':node.get_display_name().Text,
                 'BrowseName':node.get_browse_name().to_string(),
                 'value':get_node_value(node),
                 'config':wrapdata(ApiHandler.clientdata.get(nodeid,))
        }
    
    class NodeHandler(object):
        def __init__(self, nodeid):
            self.nodeid = nodeid
        def event_notification(self, event):
            from wsserver import ChannelSocketHandler
            ChannelSocketHandler.send_data('opc', {
                'nodeid': event.SourceNode.to_string(),
                'value':str(event)
                }, 'event')
        def datachange_notification(self, node, val, data):
            from wsserver import ChannelSocketHandler
            ChannelSocketHandler.send_data('opc', {
                'nodeid': node.nodeid.to_string(),
                'value':str(val)
                }, 'datachange')
        
    def api_set_node(self, nodeid, prop, value):
        if str(value).upper() == 'FALSE':
            value = False
        if nodeid not in ApiHandler.clientdata:
            ApiHandler.clientdata[nodeid] = {}
        if prop == 'data':
            if value:
                handler = ApiHandler.NodeHandler(nodeid)
                subscription = ApiHandler.client.create_subscription(10, handler)
                subid = subscription.subscribe_data_change(self.opc_get_node(nodeid))
                ApiHandler.clientdata[nodeid][prop] = (subscription, handler, subid)
            elif ApiHandler.clientdata[nodeid].get(prop):
                subscription, handler, subid = ApiHandler.clientdata[nodeid][prop]
                subscription.unsubscribe(subid)
                ApiHandler.clientdata[nodeid][prop] = None
        elif prop == 'event':
            if value:
                handler = ApiHandler.NodeHandler(nodeid)
                subscription = ApiHandler.client.create_subscription(10, handler)
                subid = subscription.subscribe_events(self.opc_get_node(nodeid))
                ApiHandler.clientdata[nodeid][prop] = (subscription, handler, subid)
            elif ApiHandler.clientdata[nodeid].get(prop):
                subscription, handler, subid = ApiHandler.clientdata[nodeid][prop]
                subscription.unsubscribe(subid)
                ApiHandler.clientdata[nodeid][prop] = None

def main():
    from tornado.options import options, define
    from wsserver import ChannelSocketHandler
    define('port', type=int, default=8000)
    tornado_app = tornado.web.Application([
               (r"/ws/(?P<channel>\S+)", ChannelSocketHandler),
               (r"/api/(?P<apiname>\S+)", ApiHandler),
               (r"/", IndexHandler),
               ],
            static_path=os.path.join(os.path.dirname(__file__), 'static'),
            debug=True
    )
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port, address='0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    # listen Ctrl+C begin
    import signal
    import sys
    ApiHandler.clearOpc()
    def handler(signal_num, frame):
        print 'Exit!'
        sys.exit(signal_num)
    signal.signal(signal.SIGINT, handler)
    print 'Ctrl+C to exit...'
    # End
    main()
