#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""pipeline pool
@author: Fibrizof(dfang84@gmail.com)
"""

import threading
import Queue

class PipelinePoolError(Exception):
    pass

class ThreadWorker(object):
    def __init__( self, threadnum, schedule_queue ):

        self.threadnum = threadnum
        self.q = Queue.Queue()
        #用来挂回整体调度队列的
        self.schedule_queue = schedule_queue

        self.ts = [ threading.Thread( target=self.run )
                    for i in range(threadnum) ]

        for t in self.ts :
            t.setDaemon(True)
            t.start()

    def run( self ):

        while True :
            r = self.q.get()
            try:
                result = r.next()
            except StopIteration as e:
                result = None
            except Exception as e:
                result = None
            self.schedule_queue.put((result, r))
            self.q.task_done()

        return

    def put(self, work):
        self.q.put( work )
        return

class PipelinePool(object):
    def __init__(self, pipeline_conf):
        self.pipelines = {}
        self.count_q = Queue.Queue()
        self.schedule_queue = Queue.Queue()
        for k,v in pipeline_conf.items():
            self.pipelines[k] = ThreadWorker(v, self.schedule_queue)
        if '_start' not in self.pipelines:
            self.pipelines['_start'] = ThreadWorker(1, self.schedule_queue)

        # _main is a schedule thread
        self.pipelines['_main'] = threading.Thread(target=self.schedule_loop)
        self.pipelines['_main'].setDaemon(True)
        self.pipelines['_main'].start()

    def schedule_loop(self):
        while True:
            #choose is which thread pool choosed
            choose, r = self.schedule_queue.get()
            if not choose:
                self.count_q.task_done()
                continue
            self.pipelines[choose].put(r)

    def put(self, func, arg):
        #r is a generator
        r = func(arg)
        self.count_q.put(r)
        self.pipelines['_start'].put(r)
        return

    def _call_raise_( self, work ):
        raise PipelinePoolError, 'Pool has been joined'

    def join( self ):
        self.__call__ = self._call_raise_
        self.count_q.join()
        return

if __name__ == '__main__' :

    class SomeClass(object):
        @staticmethod
        def somefunc(x):
            import time
            import thread
            print thread.get_ident(), x, ":1"
            time.sleep(1)
            yield "p1"
            time.sleep(1)
            print thread.get_ident(), x, ":2"
            yield "p2"
            print thread.get_ident(), x, ":3"
            return

    pipe_dict = dict(p1=1, p2=2)
    pp = PipelinePool(pipe_dict)
    [pp.put(SomeClass.somefunc, i) for i in range(5)]
    pp.join()