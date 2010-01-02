=========================
 Easychecker
=========================




 Designs
=========================

A simple way to share data in multiprocess.

There is two way to share an object in multiprocess in python. One is using
Manager process ::

    from multiprocessing import Process, Manager
    
    def f(d, l):
        d[1] = '1'
        d['2'] = 2
        d[0.25] = None
        l.reverse()
    
    if __name__ == '__main__':
        manager = Manager()
    
        d = manager.dict()
        l = manager.list(range(10))
    
        p = Process(target=f, args=(d, l))
        p.start()
        p.join()
    
        print d
        print l

Manager process is standalone process, it not under your control, it means that
you can't debug it, and if the manager has existed, only a error raised in the
requester, no way to remedy.

Another is using sharedctype ::

    from multiprocessing import Process, Value, Array

    def f(n, a):
        n.value = 3.1415927
        for i in range(len(a)):
            a[i] = -a[i]
    
    if __name__ == '__main__':
        num = Value('d', 0.0)
        arr = Array('i', range(10))
    
        p = Process(target=f, args=(num, arr))
        p.start()
        p.join()
    
        print num.value
        print arr[:]

it worked same as C language, no risks. but you must translate your object to
C data type.

We need a way to share python data type and without the manager process.
so, I wanted to integrated the json, pickle and sharedctype.
it must be using easy, like this ::

    >>> v = Share()
    
    >>> # set value
    >>> Share.value = [1,2,3,]
    
    >>> # get value
    >>> Share.value
    [1, 2, 3]
    
.. Note ::

    In current, only supported json. 