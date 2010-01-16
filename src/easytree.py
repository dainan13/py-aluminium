


import new

def breadth_first_traversal( _old ):
    
    s = []
    
    def _savenode( *args, **kwargs ):
        s.append( (args,kwargs) )
    
    newglobal = _old.func_globals.copy()
    newglobal[_old.__name__] = _savenode
    
    _oldBF = new.function( _old.func_code, newglobal )
    
    def _new( *args, **kwargs ):
        
        s.append( (args,kwargs) )
        
        while( len(s)!=0 ):
            a, kwa = s.pop(0)
            _oldBF( *a, **kwa )
    
    _new._decorator = _old
    _new.__name__ = _old.__name__
    _new.__doc__  = _old.__doc__
    
    return _new



if __name__ == '__main__':
    
    def fooDFS ( tree ):
        
        if tree == None :
            return
        
        print tree[1]
        
        fooDFS( tree[0] )
        fooDFS( tree[2] )
        
    #      1
    #    /   \
    #   2     5
    #  / \   /
    # 3   4 6
    
    t = ( ( ( None, 3, None ), 2, ( None, 4, None ) ) ,
          1,
          ( ( None, 6, None ), 5 , None )
        )
    
    print 'print the tree by depth first traversal ( preorder )'
    fooDFS(t)
    # 1 2 3 4 5 6
    
    print 
    
    # translate the DepthFirstTraversal function to BreadthFirstTraversal
    fooBFS = breadth_first_traversal( fooDFS )
    
    print 'print the tree by breadth first traversal'
    fooBFS(t)
    # 1 2 5 3 4 6
    
    