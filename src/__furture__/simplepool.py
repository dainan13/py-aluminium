#!/usr/bin/env python

"""simple thread pool
@author: dn13(dn13@gmail.com)
@author: Fibrizof(dfang84@gmail.com)
"""

import threading
import Queue
import new

def WorkerPoolError( Exception ):
    pass

class Task(threading.Thread):

    def __init__(self, queue, result_queue):
        threading.Thread.__init__(self)
        self.queue = queue
        self.result_queue = result_queue
        self.running = True

    def cancel(self):
        self.running = False
        self.queue.put(None)

    def run(self):
        while self.running:
            call = self.queue.get()
            if call:
                try:
                    reslut = call()
                    self.result_queue.put(reslut)
                except:
                    pass
            self.queue.task_done()

class WorkerPool( object ):
    
    def __init__( self, threadnum ):
        
        self.threadnum = threadnum
        self.q = Queue.Queue()
        self.result_q = Queue.Queue()

        self.ts = [ Task(self.q, self.result_q) for i in range(threadnum) ]
        
        self._registfunctions = {}
        
        self.is_in_join = False
        
        for t in self.ts :
            t.setDaemon(True)
            t.start()

    def __del__(self):
        try:
            # 调用两次的意义在于, 第一次将所有线程的running置成false, 在让他们发一次queue的信号
            # 偷懒没有写成两个接口
            for t in self.ts:
                t.cancel()
            for t in self.ts:
                t.cancel()
        except:
            pass

    def __call__( self, work ):
        if not self.is_in_join:
            self.q.put( work )
        else:
            raise WorkerPoolError, 'Pool has been joined'
    
    def join( self ):
        self.is_in_join = True
        self.q.join()
        self.is_in_join = False
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

    def get_all_result(self):
        result_list = []
        while True:
            try:
                result_list.append(self.result_q.get_nowait())
            except Exception as e:
                if 0 == self.result_q.qsize():
                    break
                else:
                    continue
        return result_list

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
    
    
