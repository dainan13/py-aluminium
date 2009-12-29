
def type_object( lines ):
    
    lines = [ l.split( ':' , 1 ) for l in lines ]
    lines = [ ( k.strip(), v.strip() ) for k, v in lines ]
    
    return dict(lines), {}

def type_table( lines ):
    
    if lines[0].startswith('!') :
        
        head = lines[0]
        lines = lines[1:]
        
        splitter = [ n for n, i in enumerate(head) if i == '!' ]
        splitter = [ (s,e) for s,e in zip( splitter , splitter[1:] + [None,] ) ]
        
        phares = [ n for n, l in enumerate(lines)
                   if l[splitter[0][0]]!='!' ]
        
        phares = zip( phares, phares[1:]+[None,] )
        
        lines = [ [ l[s:e] for s,e in splitter ]
                  for l in lines ]
        
        lines = [ [ l[0][1:] if l[0].startswith('!') else l[0], ] + l[1:]
                  for l in lines ]
        
        lines = [ [ i.strip() for i in l ] for l in lines ]
        
        lines = [ [ '\r\n'.join(c).strip('\r\n') for c in zip(*lines[s:e]) ]
                  for s, e in phares ]
        
        return lines, {'columns': [ h.strip()
                                    for h in head.strip().split('!')][1:] }
    
    maxlen = max( [ len(l) for l in lines ] )
    lines = [ l.ljust(maxlen) for l in lines ]
    columns = zip(*lines)
    columns = [ ''.join(c).strip() for c in columns ]
    
    shadow = [ c=='' for c in columns ]
    
    chead = zip( [True,]+shadow, shadow, range(0, len(shadow)) )
    chead = [ n for u, c, n in chead if u and ( not c ) ]
    
    ctail = zip( shadow, shadow[1:]+[True,], range(0, len(shadow)) )
    ctail = [ n for c, d, n in ctail if d and ( not c ) ]
    
    columns = zip( chead, ctail )
    
    lines = [ [ l[s:e+1].strip() for s,e in columns ] for l in lines ]
    
    return lines, {}
    
def type_value( lines ):
    return '\r\n'.join([ x.strip() for x in lines ]),{}

allformater = dict([ (k[5:],v) for k,v in locals().items()
                           if k.startswith('type_') ])

class EasyDocstringError( Exception ):
    """
    Error of EasyDocstriong Modules
    """
    pass

def covertformate( string ):
    
    name, type_ = string.rsplit('.' , 1 )
    
    type_ = type_.lower()
    
    name = name.strip('.').strip()
    
    if type_ == '' :
        return [name, None]
    
    if type_ not in allformater :
        raise Exception, 'not this formatter %s ' % (type_,)
    
    return [name, type_]

def parsedocstring( docstring ):
    
    dcs = docstring.splitlines()
    dcs = [ line.strip(' ') for line in dcs ]
    
    isempty = [ line == '' for line in dcs ]
    
    ghead = zip( [True,]+isempty, isempty, range(0, len(isempty)) )
    ghead = [ n for u, c, n in ghead if u and ( not c ) ]
    
    gtail = zip( isempty, isempty[1:]+[True,], range(0, len(isempty)) )
    gtail = [ n for c, d, n in gtail if d and ( not c ) ]
    
    graphs = [ dcs[h:t+1] for h,t in zip(ghead, gtail) ]
    graphs = [ covertformate(g[0][4:].strip()) + [ g[1:], ]
               for g in graphs if g[0].startswith('##!#') ]
    
    graphs = [ [n,] + list( allformater[t](b) )
               for n, t, b in graphs if n != None ]
    
    graphs = [ ( ( n, v ), ( n, ex ) ) for n, v, ex in graphs ]
    
    if graphs == [] :
        return {}
    
    graphs, graphexs = zip(*graphs)
    
    graphexs = [ [ ( n+'__'+exk , exv ) for exk, exv in ex.items() ]
                 for n, ex in graphexs ]
    
    graphexs = sum( graphexs, [] )
    
    graphs = graphexs + list(graphs)
    
    return dict(graphs)
    
def dicttable( object, key ):
    
    values = object[key]
    
    keys = object[ key + '__columns' ]
    
    return [ dict(zip( keys, v )) for v in values ]
    
if __name__=='__main__':
    
    d = '''
        insert the file infomation to a project
        
        ##!# Metas                                                       .object
        name : put_file
        classification : index
        version : 1.1
        compatible : 1.1
        author : d13
        last-modified : 2009/10/16
        
        ##!# Metas2                                                       .value
        array(
            #.MachineID   : hex(32),
            #.MachineName : ascii(-32),
            #.Info        : string,
            #.IPs         : array(string),
        )
        
        ##!# Arguments                                                    .table
        !Name          !Format                      !Required  !Default
        Project        ascii(<255)                  No
        ProjectID      number                       No
        Key            string(<1024)                Yes
        Cover          bool                         No         False
        Owner          alnum(20)                    No
        Requester      alnum(20)                    No         Anonymouse
        ACL            object(alnum(20):array(acl)) No         {}
        MD5            hex(32)                      Yes
        Size           number                       Yes
        Origo          ascii(<255)                  Yes
        Last-Modified  datetime                     Yes
        File-Meta      object                       Yes
        Ext-Meta       object                       Yes
        
        ##!# Arguments2                                                   .table
        Project        ascii(<255)          34677         No    D
        ProjectID      number   db             34         No
        Key            string(<1024)          234         Yes
        
        ##!# Arguments3                                                   .table
        !Name          !Format                      !Required  !Default
        Project        object(                      No
        !                 #.number:string
        !              )
        ProjectID      number                       No
        '''
        
    from pprint import pprint
    pprint(parsedocstring(d))

    
