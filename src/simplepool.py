

import threading
import Queue
import new

def WorkerPoolError( Exception ):
    pass

class WorkerPool( object ):
    
    def __init__( self, threadnum ):
        
        self.threadnum = threadnum
        self.q = Queue.Queue()
        
        self.ts = [ threading.Thread( target=self.run )
                    for i in range(threadnum) ]
        
        self._registfunctions = {}
        
        for t in self.ts :
            t.setDaemon(True)
            t.start()
            
        
    def run( self ):
        
        while True :
            self.q.get()()
            self.q.task_done()
        
        return
    
    def __call__( self, work ):
        
        self.q.put( work )
        
        return
    
    def _call_raise_( self, work ):
        
        raise WorkerPoolError, 'Pool has been joined'
    
    def join( self ):
        
        self.__call__ = self._call_raise_
        
        self.q.join()
        
        #for t in self.ts :
        #    t.join()
        
        return
    
    def runwithpool( self, _old ):
        
        def _new( *args, **kwargs ):
            self.q.put( lambda : _old( *args, **kwargs ) )
        
        return _new
    
    def registtopool( self, _old ):
        
        if _old.__name__ in self._registfunctions :
            raise WorkerPoolError, 'function name exists'
        
        self._registfunctions[_old.__name__] = _old
        
        return _old
        
    def __getattr__( self, name ):
        
        if name in self._registfunctions :
            return self._registfunctions[name]
        
        raise AttributeError, '%s not found' % name
    
    
if __name__ == '__main__' :
    
    import thread
    
    p = WorkerPool(5)
    
    @p.runwithpool
    def foo( a ):
        
        print 'foo>', thread.get_ident(), '>', a
        
        return
    
    @p.registtopool
    def bar( b ):
        
        print 'bar>', thread.get_ident(), '>', b
        
    
    for i in range(10):
        foo(i)
        p.bar(i+100)
        
    p( lambda : bar(200) )
    
    p.join()
    
    