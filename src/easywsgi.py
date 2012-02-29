
from wsgiref.simple_server import make_server

import pprint
import types
import inspect

import urllib
import json


class WorkError( Exception ):
    pass

class NotFound( WorkError ):
    pass



class Work(dict):
    pass

def work( url, verb='GET', resp='json', status='200 OK' ):
    
    def _work( w ):
        return Work({'verb':verb, 'url':url, 'status':status, 'resptype':resp, 'work':w})
    
    return _work



class Error(dict):
    pass

def error( et, resp=None, status='500 Server Error' ):
    
    def _error( w ):
        return Error({'error':et, 'status':status, 'resptype':resp, 'work':w})
    
    return _error



class Response(dict):
    pass

def resp( resp ):
    
    def _resp( w ):
        return Response({'resp':resp, 'work':w})
    
    return _resp



class WObject(dict):
    
    def method(self, name, verb, resp='json', status='200 OK' ):
        
        def _method(w):
            self['methods'][(verb,name)] = \
                                { 'status':status, 'resptype':resp, 'work':w }
            return w
            
        return _method

def obj( urlprefix ):
    
    def _obj( o ):
        return WObject({ 'url':urlprefix, 'work':o, 'methods': {} })
    
    return _obj


class MetaServer( type ):
    
    def __new__ ( cls, name, bases, attrs ):
        
        alist = attrs.items() 
        
        metas, methods = MetaServer.split_method_and_meta( alist, Work )
        attrs.update(methods)
        metas = [ ( ( m.pop('verb'), m.pop('url') ) , m ) for m in metas ]
        metas = dict(metas)
        attrs['workentrys'] = MetaServer.get_attr( attrs, bases, 'workentrys') or {}
        attrs['workentrys'].update(metas)
        
        metas, methods = MetaServer.split_method_and_meta( alist, Error )
        attrs.update(methods)
        metas = [ (m.pop('error'),m) for m in metas ]
        metas = dict(metas)
        attrs['errorentrys'] = MetaServer.get_attr( attrs, bases, 'errorentrys') or {}
        attrs['errorentrys'].update(metas)
        
        metas, methods = MetaServer.split_method_and_meta( alist, Response )
        attrs.update(methods)
        metas = [ (m.pop('resp'),m) for m in metas ]
        metas = dict(metas)
        attrs['response'] = MetaServer.get_attr( attrs, bases, 'response') or {}
        attrs['response'].update(metas)
        
        antiattrs = dict( (v,k) for k, v in attrs.items() 
                          if MetaServer.hashable(v) )
        
        metas, methods = MetaServer.split_method_and_meta( alist, WObject )
        attrs.update(methods)
        metas = [ (m.pop('url'),m) for m in metas ]
        for u, m in metas :
            for me in m['methods'].values() :
                me['work'] = antiattrs[me['work']] 
                                 
        attrs['objentrys'] = MetaServer.get_attr( attrs, bases, 'objentrys') or []
        attrs['objentrys'].extend( metas )
        
        return type.__new__( cls, name, bases, attrs )
    
    @staticmethod
    def hashable( i ):
        try :
            hash(i)
            return True
        except :
            return None
    
    @staticmethod
    def split_method_and_meta( alist, t ):
        metas = [ (k,v) for k, v in alist if type(v) == t ]
        methods = [ (k,v.pop('work')) for k, v in metas ]
        for k, v in metas :
            v['work'] = k
        return ( zip(*metas)[1] if metas else [] ), dict(methods)
        
    @staticmethod
    def get_attr( attrs, bases, name ):
        
        if name in attrs :
            return attrs[name]
            
        for b in bases :
            try :
                r = getattr( bases[0], name )
                if type(r) == types.ListType :
                    return r[:]
                elif type(r) == types.DictType :
                    return r.copy()
                else :
                    return r
            except AttributeError, e:
                pass
                
        return 



class Server( object ):
    
    __metaclass__ = MetaServer
    
    workentrys = {}
    errorentrys = {}
    objentrys = []
    response = {}
    
    staticroot = './'
    
    def make_workentry( self, env ):
        
        qs = env['QUERY_STRING'].split('&')
        
        method = ''
        
        if qs and '=' not in qs[0] :
            method = qs[0]
            qs = [x.split('=',1) for x in qs[1:]]
        else :
            qs = [x.split('=',1) for x in qs]
            
        qs = dict( (k, urllib.unquote(v)) for k, v in qs )
        
        
        for urlprefix, obj in self.objentrys:
            if env['PATH_INFO'].startswith( urlprefix ):
                return self.make_objentry( urlprefix, obj, method, env, qs )
        
        try :
            r = self.workentrys[(env['REQUEST_METHOD'], env['PATH_INFO'])]
            return None, r['work'], qs, r['status'], r['resptype']
        except KeyError, e :
            pass
            
        try :
            r = self.workentrys[(None, env['PATH_INFO'])]
            return None, r['work'], qs, r['status'], r['resptype']
        except :
            pass
        
        raise NotFound, 'not found'
    
    def make_objentry( self, urlprefix, objinfo, method, env, qs ):
        
        try :
            obj = getattr( self, objinfo['work'])( env['PATH_INFO'][len(urlprefix):] )
            m = objinfo['methods'][(env['REQUEST_METHOD'],method)]
        
            return obj, m['work'], qs, m['status'], m['resptype']
        except KeyError, e :
            raise NotFound, 'not found'
    
    def make_errorentry( self, e, env ):
        
        et = e.__class__
        
        ee = None 
        while( ee == None ):
            ee = self.errorentrys.get(et,None)
            et = et.__base__
            if et == None :
                raise
        
        return ee['work'], ee['status'], ee['resptype']
    
    def make_response( self, rtype ):
        
        return self.response[rtype]
    
    def run( self, env, start_response ):
        
        r = None
        
        try :
            obj, work, args, status, resp = self.make_workentry(env)
            work = getattr( self, work )
            
            obj = [obj] if obj else []
            
            headers, r = work(*obj, **args)
            
        except Exception, e:
            work, status, resp = self.make_errorentry( e, env )
            work = getattr( self, work )
            headers, r = work()
            
        if resp :
            resp = getattr( self, resp )
            r = resp( headers, r )
        
        start_response( status, headers )
        
        yield r
        
        return
        
    @resp('json')
    def json( self, headers, r ):
        return json.dumps(r)
        
    @resp('raw')
    def raw( self, headers, r ):
        return r
        
    @resp('static')
    def static( self, headers, r ):
        with open( self.staticroot + r, 'r' ) as fp :
            return fp.read()
        raise NotFound, 'static file not found'
        
    @resp(None)
    def none( self, headers, r ):
        return ''
        
    __call__ = run
    
    @error( NotFound, status='404 NOT FOUND' )
    def notfound( self ):
        return [], ''
    
    
    def httpd( self, host, port ):
        
        httpd = make_server( '', 9000, self.run )
        httpd.serve_forever()
        
        return
    
    
if __name__ in ('uwsgi_file_index','__main__') :
    
    class Test(Server):
        
        @work( '/', 'GET', 'json' )
        def index( self, **kwargs ):
            return [], ['hello','world',{'args':kwargs}]
            
        @obj( '/path/' )
        def upath( self, inp ):
            return str(inp)
        
        @upath.method('', 'GET', 'json')
        def upath_get( self, obj ):
            return [], obj
        
        @upath.method('split', 'GET', 'json')
        def upath_split( self, obj ):
            return [], obj.split('/')
            
    
if __name__ == 'uwsgi_file_index' : 
    
    t = Test()
    application = t.run
    
elif __name__ == '__main__' :
    
    t = Test()
    t.httpd()

    
    
    
    
    
    