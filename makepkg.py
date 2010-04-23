import sys
import os
import tempfile


# A simple tool to make package


def system( s ):
    print '>>>', s
    return os.system( s )

if __name__ == '__main__' :
    
    #ver = int(sys.args[1])
    system( 'svn up' )
    a, b = os.popen2( 'svn info' )
    b = b.read()
    b = [ l.split(': ', 1 ) for l in b.splitlines() ]
    ver = int(b[4][1])
    
    #tmpdir = tempfile.gettempdir() 
    tmpdir = tempfile.mkdtemp()
    
    aimdir = '%s/aluminium-prealpha.r%d' % ( tmpdir , ver )
    aimtar = 'aluminium-prealpha.r%d' % ( ver, )
    
    system( 'svn export ./ %s' % ( aimdir ) )
    system( 'tar -C %s/ -czf %s.tar.gz %s ' % ( tmpdir, aimtar, aimtar  ) )

