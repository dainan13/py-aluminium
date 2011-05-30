
from Al import easydoc

def makeuptree( l ):
    
    ns = [ n for n, i in enumerate(l) if i[0] == l[0][0] ]
    ns = zip( ns, ns[1:]+[None,] )
    r = [ (l[s],l[s+1:e]) for s, e in ns ]
    
    return [ (k[1], makeuptree(v)) for k, v in r ]
    

def xmltrans( node ):
    
    name = node[0]['XML'].strip()
    
    is_options = name.startswith('[')
    
    name = name.strip('[]')
    
    is_inline = name.startswith('(')
    
    name = name.strip('()')
    
    childs = [ ( child[0]['XML'].strip(), child ) for child in node[1] ]
    
    realchilds = [ ( ck, xmltrans(cv) ) 
                   for ck, cv in childs 
                   if not ck.startswith('(')
                 ]
                 
    inlinechilds = [ ( ck.strip('()'), xmltrans(cv) ) 
                     for ck, cv in childs 
                     if ck.startswith('(')
                   ]
    
    if realchilds == [] :
        
        if is_inline and node[0]['C'] :
            _r = ' '+name+'='+'"'+node[0]['C']+'"'
            def node_trans( r, s3c ):
                return [_r,]
        elif is_inline and node[0]['R']:
            _r = ' '+name + '="'
            k, rn = ( node[0]['R'].strip().split('|',1) + [''] ) [:2]
            k = k.strip()
            k = None if k == '@' else k
            k = int(k.strip('$')) if k and k.startswith('$') else k
            rn = datatrans.get( rn ) if rn.strip() else lambda x : x
            def node_trans( r, s3c ):
                if k is None :
                    return [_r,unicode(rn(r)),'"']
                return [_r,unicode(rn(r[k])),'"'] if ( not is_options ) or k in r else []
        elif is_inline and node[0]['S3C']:
            _r = ' '+name + '="'
            k, s3cn = ( node[0]['S3C'].strip().split('|',1)+ [''] ) [:2]
            k = k.strip()
            k = None if k == '@' else k
            k = int(k.strip('$')) if k and k.startswith('$') else k
            s3cn = datatrans.get( s3cn ) if s3cn.strip() else lambda x : x
            def node_trans( r, s3c ):
                if k is None :
                    return [_r,unicode(s3cn(s3c)),'"']
                return [_r,unicode(s3cn(s3c[k])),'"'] if ( not is_options ) or k in s3c else []
        elif (not is_inline) and node[0]['C']:
            _r = '<'+name+'>'+node[0]['C']+'</'+name+'>'
            def node_trans( r, s3c ):
                return [_r,]
        elif (not is_inline) and node[0]['R']:
            _rl = '<'+name
            _rr = '</'+name+'>'
            k, rn = ( node[0]['R'].strip().split('|',1) + [''] ) [:2]
            k = k.strip()
            k = None if k == '@' else k
            k = int(k.strip('$')) if k and k.startswith('$') else k
            rn = datatrans.get( rn ) if rn.strip() else lambda x : x
            def node_trans( r, s3c ):
                
                if k is None :
                    return ( [_rl,] + \
                             sum([ ic[1](r,s3c) for ic in inlinechilds ],[]) + \
                             ['>',unicode(rn(r)),_rr] )
                    
                return ( [_rl,] + \
                         sum([ ic[1](r,s3c) for ic in inlinechilds ],[]) + \
                         ['>',unicode(rn(r[k])),_rr] ) if ( not is_options ) or k in r else []
        elif (not is_inline) and node[0]['S3C']:
            _rl = '<'+name
            _rr = '</'+name+'>'
            k, s3cn = ( node[0]['S3C'].strip().split('|',1)+ [''] ) [:2]
            k = k.strip()
            k = None if k == '@' else k
            k = int(k.strip('$')) if k and k.startswith('$') else k
            s3cn = datatrans.get( s3cn ) if s3cn.strip() else lambda x : x
            def node_trans( r, s3c ):
                
                if k is None :
                    return ( [_rl,] + \
                             sum([ ic[1](r,s3c) for ic in inlinechilds ],[]) + \
                             ['>',unicode(s3cn(s3c)),_rr] )
                
                return ( [_rl,] + \
                         sum([ ic[1](r,s3c) for ic in inlinechilds ],[]) + \
                         ['>',unicode(s3cn(s3c[k])),_rr] ) if ( not is_options ) or k in s3c else []
        
        else :
            raise Exception, 'Can not reach here.'
    
    else :
        
        rf = node[0]['R'].startswith('%')
        rk, rx = ( node[0]['R'].strip('%').split('|',1)+[' '] ) [:2]
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
        
        s3cf = node[0]['S3C'].startswith('%')
        s3ck, s3cx = ( node[0]['S3C'].strip('%').split('|',1)+[' '] ) [:2]
        s3ck = s3ck.strip()
        s3cx = s3cx.strip()
        
        s3cx = datatrans.get( s3cx ) if s3cx else lambda x : x
        
        if s3cf and s3ck :
            s3cn = lambda x : s3cx(x[s3ck])
        elif s3cf and not s3ck :
            s3cn= lambda x : s3cx(x)
        elif not s3cf and s3ck :
            s3cn = lambda x : [s3cx(x[s3ck]),]
        else :
            s3cn = lambda x : [s3cx(x),]
        
        _rl = '<'+name
        _rr = '</'+name+'>'
        
        #def node_trans( r, s3c ):
        def node_trans( datas ):
            
            return  sum( [ [_rl,] + \
                           sum([ ic[1](xr,xs3c) for ic in inlinechilds ],[]) + \
                           [ '>' ] + \
                           sum( [ rc[1](xr,xs3c) 
                                  for rc in realchilds 
                                ], [] ) + \
                           [ _rr ]
                          for xr in rn(r) 
                          for xs3c in s3cn(s3c)
                         ], [] )
                    
    
    return node_trans
    
    
    
if __name__ == "__main__" :
    
    d = easydoc.parse ("""
    ##!# test                                                             .Table
    !XML                          !R                   !S3C            !C                                           !example-commnets
    channel                          
      title                                                            SinaStorage Statistics 
      description                                      Project
      lastBuildDate                                    Update
      pubDate                                          Update
      item                        %
        title                                                          SinaStorage Statistics
        description                 @|statweb
        guid                        Log-Time|md5x_uuid
        pubDate                     Log-Time
    """)
    
    v = d['test'].todict()
    
    v = [ ( i['XML'].rstrip().count(' '), i ) for i in v ]
    from pprint import pprint
    pprint( makeuptree(v) )
    
    