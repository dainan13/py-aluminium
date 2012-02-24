import pprint
import types

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
        
        return type.__new__( cls, name, bases, attrs )
    
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
    response = {}
    
    def make_workentry( self, env ):
        
        try :
            r = self.workentrys[(env['REQUEST_METHOD'],env['PATH_INFO'])]
            return r['work'], r['status'], r['resptype']
        except KeyError, e :
            pass
            
        try :
            r = self.workentrys[(None,env['PATH_INFO'])]
            return r['work'], r['status'], r['resptype']
        except :
            pass
        
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
        
        work, status, resp = self.make_workentry(env)
        work = getattr( self, work )
        
        r = None
        
        try :
            headers, r = work()
        except Exception, e:
            work, status, resp = self.make_errorentry( e, env )
            work = getattr( self, work )
            headers, r = work()
            return
            
        if resp :
            resp = getattr( self, resp )
            r = resp( headers, r )
        
        start_response( status, headers )
        
        yield r
        
        return
        
    @resp('json')
    def json( self, headers, r ):
        return json.dumps(r)
        
    @resp(None)
    def none( self, headers, r ):
        return ''
        
    __call__ = run
    
    
if __name__ in ('uwsgi_file_index','__main__') :
    
    class Test(Server):
        
        @work( '/', 'GET', 'json' )
        def index( self ):
            
            return [], ['hello','world']
            
            
    
if __name__ == 'uwsgi_file_index' : 
    
    t = Test()
    application = t.run
    
elif __name__ == '__main__' :
    
    from wsgiref.simple_server import make_server
    
    t = Test()
    httpd = make_server( '', 8000, t.run )
    
    print "Serving on port 8000..."
    httpd.serve_forever()

    
    
    
    
    
    