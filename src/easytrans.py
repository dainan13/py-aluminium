
import types
import xml.sax.saxutils
from Al import easydoc


def makeuptree( l ):
    
    ns = [ n for n, i in enumerate(l) if i[0] == l[0][0] ]
    ns = zip( ns, ns[1:]+[None,] )
    r = [ (l[s],l[s+1:e]) for s, e in ns ]
    
    return [ (k[1], makeuptree(v)) for k, v in r ]
    

def xmltrans( node, datatrans, target='XML' ):
    
    name = node[0][target].strip()
    
    is_options = name.startswith('[')
    
    name = name.strip('[]')
    
    is_inline = name.startswith('(')
    
    name = name.strip('()')
    
    childs = [ ( child[0][target].strip(), child ) for child in node[1] ]
    
    realchilds = [ ( ck, xmltrans(cv, datatrans, target) ) 
                   for ck, cv in childs 
                   if not ck.startswith('(')
                 ]
                 
    inlinechilds = [ ( ck.strip('()'), xmltrans(cv, datatrans, target) ) 
                     for ck, cv in childs 
                     if ck.startswith('(')
                   ]
    
    d = [ (k, v) for k, v in node[0].items() if v.strip() != '' and v!=target ]
    
    if len(d) != 1 :
        raise Exception, 'doc error'
    
    k, v = d[k]
        
    
    if realchilds == [] :
        
        if is_inline :
            
            _r = ' '+name + '="'
            xk, rn = ( v.strip().split('|',1) + [''] ) [:2]
            xk = xk.strip()
            xk = None if xk == '@' else xk
            xk = int(xk.strip('$')) if xk and xk.startswith('$') else xk
            rn = datatrans.get( rn ) if rn.strip() else lambda x : x
            
            def node_trans( datas ):
                if xk is None :
                    return [_r,unicode(rn(datas[k])),'"']
                return [_r,unicode(rn(datas[k][xk])),'"'] if ( not is_options ) or xk in datas[k] else []
            
        else :
            
            _rl = '<'+name
            _rr = '</'+name+'>'
            xk, rn = ( v.strip().split('|',1) + [''] ) [:2]
            xk = xk.strip()
            xk = None if xk == '@' else xk
            xk = int(xk.strip('$')) if xk and xk.startswith('$') else xk
            rn = datatrans.get( rn ) if rn.strip() else lambda x : x
            
            def node_trans( datas ):
                
                if xk is None :
                    return ( [_rl,] + \
                             sum([ ic[1](datas) for ic in inlinechilds ],[]) + \
                             ['>',unicode(rn(datas[k])),_rr] )
                    
                return ( [_rl,] + \
                         sum([ ic[1](datas) for ic in inlinechilds ],[]) + \
                         ['>',unicode(rn(datas[k][xk])),_rr] ) if ( not is_options ) or xk in datas[k] else []
                             
    
    else :
        
        rf = v.startswith('%')
        rk, rx = ( v.strip('%').split('|',1)+[''] ) [:2]
        rk = rk.strip()
        rx = rx.strip()
        
        rx = datatrans.get( rx ) if rx else lambda x : x
        
        if rf and rk :
            rn = lambda x : rx(x[rk])
        elif rf and not rk :
            rn = lambda x : rx(x)
        elif not rf and rk :
            rn = lambda x : [rx(x[rk]),]
        else :
            rn = lambda x : [rx(x),]
        
        _rl = '<'+name
        _rr = '</'+name+'>'
        
        def node_trans( datas ):
            
            return  sum( [ [_rl,] + \
                           sum([ ic[1](dict(datas.items()+[k,xr])) for ic in inlinechilds ],[]) + \
                           [ '>' ] + \
                           sum( [ rc[1](dict(datas.items()+[k,xr])) 
                                  for rc in realchilds 
                                ], [] ) + \
                           [ _rr ]
                          for xr in rn(datas[k]) 
                         ], [] )
                    
    
    return node_trans
    
class Consts(object):
    def __getitem__( self, a ):
        return xml.sax.saxutils.escape(a)
    
consts = Consts()

def buildxmltrans( inp, datatrans=None, target='XML' ):
    
    if type(inp) in types.StringTypes :
        inp = easydoc.DEFAULT_E.parse_table( inp.strip(' ').strip('\r\n').splitlines() )
    
    v = inp.todict()
    v = [ ( i[target].rstrip().count(' '), i ) for i in v ]
    t = makeuptree(v)
    
    trans = xmltrans( v, datatrans, target )
    
    return lambda **kwargs : trans(kwargs)
    
    
if __name__ == "__main__" :
    
    xt = buildxmltrans("""
!XML    !A     !B     !C
a              p
  b     %
    c    x
    d    y
    e                 h
    """)
    
    print xt(A=[{'x':1,'y':2},{'x':3,'y':4}], B={'p':'hello'}, C=consts)
    