
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
    
    d = [ (k, v) for k, v in node[0].items() if v.strip() != '' and k!=target ]
    
    if len(d) == 0 :
        
        _rl = '<'+name
        _rr = '</'+name+'>'
        
        def node_trans( datas ):
            
            return  [_rl,] + \
                    sum([ ic[1](datas) for ic in inlinechilds ],[]) + \
                    [ '>' ] + \
                    sum( [ rc[1](datas) 
                             for rc in realchilds 
                         ], [] ) + \
                    [ _rr ]
        
        return node_trans
    
    if len(d) != 1 :
        raise Exception, ( 'doc error', d )
    
    k, v = d[0]
    
    
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
            xk = False if xk == '%' else xk
            xk = None if xk == '@' else xk
            xk = int(xk.strip('$')) if xk and xk.startswith('$') else xk
            rn = datatrans.get( rn ) if rn.strip() else lambda x : x
            
            def node_trans( datas ):
                
                if xk is False :
                    return sum( [ [_rl,] + \
                                  sum([ ic[1](dict(datas.items()+[(k,xr)])) for ic in inlinechilds ],[]) + \
                                  ['>',_rr]
                                  for xr in rn(datas[k])
                                ], [] )
                
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
                           sum([ ic[1](dict(datas.items()+[(k,xr)])) for ic in inlinechilds ],[]) + \
                           [ '>' ] + \
                           sum( [ rc[1](dict(datas.items()+[(k,xr)])) 
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
        lns = inp.strip(' ').strip('\r\n').splitlines()
        z = len(lns[0]) - len(lns[0].lstrip())
        lns = [ l[z:] for l in lns ]
        inp = easydoc.DEFAULT_E.parse_table( lns )
    
    v = inp.todict()
    v = [ ( i[target].rstrip().count(' '), i ) for i in v ]
    t = makeuptree(v)
    
    trans = xmltrans( t[0], datatrans, target )
    
    return lambda **kwargs : ''.join( trans(kwargs) )
    
    
if __name__ == "__main__" :
    
    xt = buildxmltrans("""
    !XML    !A      !B     !C
    a
      (f)           p
      b     %
        c    x|add
        d    y
        e                  h
        sum  @|sumv
    """, datatrans={ 'add': lambda x:x+10, 'sumv': lambda x: sum(x.values()) } )
    
    print xt(A=[{'x':1,'y':2},{'x':3,'y':4}], B={'p':'hello'}, C=consts)
    
    data = [{u'Log-Time': u'Tue, 31 May 2011 13:31:03 CST', u'Ref_Capacity':
93053618133399, u'File_Capacity': 93049341934167, u'Ref_Quantity':
21835317, u'Download_Capacity': 7387156286423695, u'Object_Capacity':
68418963032758, u'Group_Quantity': 8278, u'Upload_Quantity': 1596647,
u'Project_Quantity': 938, u'Object_Quantity': 17007865,
u'Download_Quantity': 10605251134, u'File_Quantity': 21834238,
u'Partition_Used_Rate': 1, u'Partition_Quantity': 57,
u'Upload_Capacity': 3500363201753}, {u'Log-Time': u'Tue, 31 May 2011 10:31:31 CST', u'Ref_Capacity': 93008311126702, u'File_Capacity':
93003670775778, u'Ref_Quantity': 21817506, u'Download_Capacity':
7383387203656727, u'Object_Capacity': 68382020015983, u'Group_Quantity':
8275, u'Upload_Quantity': 1571721, u'Project_Quantity': 936,
u'Object_Quantity': 16991916, u'Download_Quantity': 10593890921,
u'File_Quantity': 21816182, u'Partition_Used_Rate': 1,
u'Partition_Quantity': 58, u'Upload_Capacity': 3451638854023}]
    
    xt = buildxmltrans("""
    !XML        !A
    systemLog
     log        %
      x          Ref_Capacity
      y          File_Capacity
      z          Log-Time
     xxx        
      yyy       %
       (a)       Log-Time
    """)
    
    print xt(A=data)
    
    
    