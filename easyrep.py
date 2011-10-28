import easyprotocol as ezp
import pymysql
import struct
import datetime
import types
import easysqllite as esql

CnL = esql.ConnLite

class EasyRepError(Exception):
    pass

class UnkownDBArgs(EasyRepError):
    pass

class UnknownTableDefine(EasyRepError):
    pass

class UnknownColumnType(EasyRepError):
    pass

class MySQLBinLogError(EasyRepError):
    pass


class EventWait(object):
    pass


# MYSQL_TYPE_DECIMAL = 0, // decimal numeric 4 byte
# MYSQL_TYPE_TINY = 1, tinyint 1
# MYSQL_TYPE_SHORT = 2, smallint 2
# MYSQL_TYPE_LONG = 3, int 4
# MYSQL_TYPE_FLOAT = 4, 
# MYSQL_TYPE_DOUBLE = 5, 
# MYSQL_TYPE_NULL = 6, 
# MYSQL_TYPE_TIMESTAMP = 7, // 4 from_unixtime(0x)
# MYSQL_TYPE_LONGLONG = 8, bigint 8
# MYSQL_TYPE_INT24 = 9, //field_medium mediumint
# MYSQL_TYPE_DATE = 10,
# MYSQL_TYPE_TIME = 11,
# MYSQL_TYPE_DATETIME = 12,
# MYSQL_TYPE_YEAR = 13,
# MYSQL_TYPE_NEWDATE = 14,
# MYSQL_TYPE_VARCHAR = 15, //field_varstring
# MYSQL_TYPE_BIT = 16,
# MYSQL_TYPE_NEWDECIMAL = 246, new decimal mumeric
# MYSQL_TYPE_ENUM = 247, 
# MYSQL_TYPE_SET = 248,
# MYSQL_TYPE_TINY_BLOB = 249,
# MYSQL_TYPE_MEDIUM_BLOB = 250,
# MYSQL_TYPE_LONG_BLOB = 251,
# MYSQL_TYPE_BLOB = 252,
# MYSQL_TYPE_VAR_STRING = 253,
# MYSQL_TYPE_STRING = 254,
# MYSQL_TYPE_GEOMETRY = 255,
        
        
class RowType( ezp.ProtocolType ):
    
    datetimeformat = True
    
    def __init__( self ):
        
        self.name = 'rows'
        self.cname = 'rows'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
        self.sqlquery = None
        self.tablefilter = None
        
    def length( self, lens, array ):
        return None
        
    def read_multi( self, namespace, fp, lens, mlens, args ):

        raise Exception, 'can\'t read single rowtype'
        
    @staticmethod
    def roundlen( l ):
        return (l+7) / 8
        
    def readbit( self, x, l, mlens ):
        
        le = self.roundlen(mlens)
        s = x[l:l+le]
        s = [ ( (ord(r)>>i) & 1 ) for r in s for i in range(8) ]
        
        return s[:mlens], l+le
        
    def readint( self, x, l, lens, ca=True ):
        
        chrs = x[l:l+lens]
        
        r = 0
        
        for i, c in enumerate(chrs) :
            r += ord(c) * ( 256**i )
            
        if ca == False and ord(chrs[-1]) & 128 :
            r -= 2**(len(chrs)*8)
            #pass
            
        return r, l+lens
        
    def readchar( self, x, l, lens ):
        
        return x[l:l+lens], l+lens
        
    def readfloat( self, x, l, lens ):
        
        if lens == 4 :
            return struct.unpack('<f', x[l:l+lens] )[0], l+lens
        elif lens == 8 :
            return struct.unpack('<d', x[l:l+lens] )[0], l+lens
        
        raise Exception, 'float read error'
        
    
    def colparse( self, t ):
        
        if t.startswith('int'):
            return t.endswith('unsigned')
        
        if t.startswith('varchar') or t.startswith('char') :
            r = int( t.split('(',1)[1].split(')')[0] )
            return 1 if r <= 64 else 2
                
        if t.startswith('varbinary') or t.startswith('binary') :
            r = int( t.split('(',1)[1].split(')')[0] )
            return 1 if r < 256 else 2
            
        return
        
    def read( self, namespace, fp, lens, args ):
        
        #print '!', lens
        
        x = fp.read(lens)
        
        l = 0
        r = []

        columns_count, coltypes, metadatas, tst, idt, tid = args
        
        tname = idt.get(tid, None)
        
        if tname == None :
            raise Exception, ('table id error', tid)
        
        if self.tablefilter and not self.tablefilter(tname) :
            return x, lens
        
        cols = tst.get(tname, None)
        
        if not cols :
            
            if not self.sqlquery :
                raise UnknownTableDefine, '.'.join(tname)
            
            try :
                rst = self.sqlquery( 'DESCRIBE `%s`.`%s`' % tname )
            except UnkownDBArgs:
                raise UnknownTableDefine, '.'.join(tname)
            
            rst = [ (row['Field'], self.colparse(row['Type'])) for row in rst ]
            
            cols = zip(*rst)
            tst[tname] = cols
            
        fieldnames, cola = cols
        
        if columns_count != len(coltypes) :
            raise Exception, ('columns error', columns_count, coltypes)
        
        #print 'x'*10
        #print 'lens:', lens
        #print 'columns_count:', columns_count
        #print 'coltypes:', coltypes
        #print 'fieldnames:', fieldnames
        #print repr(x)
        #print 'x'*10
        
        while l < lens :
            
            isnull, l = self.readbit( x, l, columns_count )
            #print 'isnull:', isnull
            cols = zip( coltypes, metadatas, isnull, cola )
            
            rr = []
            
            for coltype, mdata, isnull, ca in cols :
                
                #_debug_l = l
                
                if isnull == 1 :
                    rr.append( None )
                    continue
                    
                if coltype == 1 : # tiny int
                    _r, l = self.readint(x,l,1,ca)
                    rr.append( _r )
                elif coltype == 2 : # small int
                    _r, l = self.readint(x,l,2,ca)
                    rr.append( _r )
                elif coltype == 3 : # int
                    _r, l = self.readint(x,l,4,ca)
                    rr.append( _r )
                elif coltype == 4 : # float
                    _r, l = self.readfloat(x,l,4)
                    rr.append( _r )
                elif coltype == 5 : # double
                    _r, l = self.readfloat(x,l,8)
                    rr.append( _r )
                elif coltype == 7 : # timestamp
                    _r, l = self.readint(x,l,4)
                    rr.append( datetime.datetime.fromtimestamp(_r) )
                elif coltype == 8 : # bigint
                    _r, l = self.readint(x,l,8,ca)
                    rr.append( _r )
                elif coltype == 9 : # medium int
                    _r, l = self.readint(x,l,3,ca)
                    rr.append( _r )
                elif coltype == 12 : # datetime
                    _r, l = self.readint(x,l,8)
                    if self.datetimeformat :
                        rr.append( None if _r < 10000101000000 else datetime.datetime.strptime(str(_r),'%Y%m%d%H%M%S') )
                    else :
                        rr.append( _r )
                elif coltype == 15 : # varchar
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 249 : # tiny blob / text
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 250 : # medium blob / text
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 251 : # long blob / text
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 252 : # blob / text
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 253 : # varbinary, may not correct, varbinary is 15 instead
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 254 : # binary / char
                    _r, l = self.readint(x,l,mdata)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                else :
                    raise UnknownColumnType, ('unkown column type',coltype)
                
                #print '.'*10
                #print coltype, ca, repr(rr[-1])
                #print repr(x[_debug_l:l])
            
            r.append(dict(zip(fieldnames,rr)))
        
        return r, lens



class PACKINTType( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'packint'
        self.cname = 'long'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def read( self, namespace, fp, lens, args ):
        
        c = ord(fp.read(1))
        
        if c < 251 :
            return c, 1
        
        if c == 251 :
            return None, 1
        
        r = 0
        
        if c == 252 :
            chrs = fp.read(2)
        elif c == 253 :
            chrs = fp.read(3)
        else :
            chrs = fp.read(8)
            
        for i, c in enumerate(chrs) :
            r += ord(c) * ( 256**i )
        
        return r, len(chrs)+1
        


class METADATAType( ezp.ProtocolType ):
    
    def __init__( self ):
        
        self.name = 'metadata'
        self.cname = 'int *'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
    def length( self, lens, array ):
        return None
    
    def readint( self, x, l, lens, bigend=False ):
        
        chrs = x[l:l+lens]
        
        r = 0
        
        if bigend == True :
            chrs = list(chrs)
            chrs.reverse()
        
        for i, c in enumerate(chrs) :
            r += ord(c) * ( 256**i )
            
        return r, l+lens
    
    def read( self, namespace, fp, lens, args ):
        
        x = fp.read(lens)
        
        l = 0
        
        rr = []
        
        for coltype in args :
            
            if coltype == 1 : # tiny int
                rr.append( None )
            elif coltype == 2 : # small int
                rr.append( None )
            elif coltype == 3 : # int
                rr.append( None )
            elif coltype == 4 : # float
                rr.append( None )
            elif coltype == 5 : # double
                rr.append( None )
            elif coltype == 7 : # timestamp
                rr.append( None )
            elif coltype == 8 : # bigint
                rr.append( None )
            elif coltype == 9 : # medium int
                rr.append( None )
            elif coltype == 12 : # datetime
                rr.append( None )
            elif coltype == 15 : # varchar
                _r, l = self.readint(x,l,2)
                rr.append( 2 if _r >= 256 else 1 )
            elif coltype == 249 : # tiny blob / text
                _r, l = self.readint(x,l,1)
                rr.append( _r )
            elif coltype == 250 : # medium blob / text
                _r, l = self.readint(x,l,1)
                rr.append( _r )
            elif coltype == 251 : # long blob / text
                _r, l = self.readint(x,l,1)
                rr.append( _r )
            elif coltype == 252 : # blob / text
                _r, l = self.readint(x,l,1)
                rr.append( _r )
            elif coltype == 253 : # varbinary, may not correct, varbinary is 15 instead
                _r, l = self.readint(x,l,2)
                rr.append( 2 if _r >= 256 else 1 )
            elif coltype == 254 : # binary / char
                _r, l = self.readint(x,l,2)
                rr.append( 1 if _r >= 65024 else 2 )
            else :
                raise UnknownColumnType, ('unkown column type',coltype)
        
        if l != lens :
            raise EasyRepError, 'metadata read error'
        
        return tuple(rr), lens


class EasyReplication(object):
    
    #dbargsort = ('host', 'port', 'user', 'passwd', 'db',)
    
    COM_BINLOG_DUMP = 18
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(RowType())
    ebp.buildintypes.append(PACKINTType())
    ebp.buildintypes.append(METADATAType())
    ebp.namespaces = dict( (bt.name, bt) for bt in ebp.buildintypes )
    ebp.parsefile( 'replication.protocol' )
    
    def __init__( self, db, location,
                        tablefilter=None, ):
        
        self.conn = pymysql.connect( **db )
        self.dbarg = db
        self.serverid = 1
        
        self.logname, self.pos, self.tablest = location or (None,None,None)
        
        if self.tablest == None :
            self.tablest = {}
            self.ebp.namespaces['rows'].sqlquery = self.executesqlone
        
        if type(tablefilter) == types.TupleType :
            
            if len(tablefilter) != 2 or tablefilter[0] == None :
                raise TypeError, 'tablefilter argument type error'
            
            if tablefilter[1] == None :
                tf = tablefilter[0]
                tablefilter = lambda x : ( x[0] == tf )
            else :
                tf = tablefilter
                tablefilter = lambda x : ( x == tf )
        
        self.tablefilter = tablefilter or ( lambda x : True )
        self.dumpfilter = lambda x : True
        self.ebp.namespaces['rows'].tablefilter = self.tablefilter
        #self.dbfilter = dbfilter or ( lambda x : True )
        
        self.run_pos = None
        
    def executesql( self, query ):
        
        cur = self.conn.cursor()
        cur.execute( query )
        dsc = cur.description
        dsc = [ d[0] for d in dsc ]
        
        rst = cur.fetchall()
        cur.close()
        
        return [ dict(zip(dsc,r)) for r in rst ]
        
    def executesqllarge( self, query ):
        
        cur = self.conn.cursor()
        cur.execute( query )
        dsc = cur.description
        dsc = [ d[0] for d in dsc ]
        
        rst = cur.fetchone()
        while rst :
            yield dict(zip(dsc,rst))
            rst = cur.fetchone()
        
        cur.close()
        
        return
        
    def executesqlone( self, query ):
        
        if self.dbarg is None :
            raise UnkownDBArgs, 'unkown db arg'
            
        conn = pymysql.connect( **self.dbarg )
        
        cur = conn.cursor()
        cur.execute( query )
        dsc = cur.description
        dsc = [ d[0] for d in dsc ]
        
        rst = cur.fetchall()
        cur.close()
        conn.close()
        
        return [ dict(zip(dsc,r)) for r in rst ]
        
    def firstdump( self, nodump = False ):
        
        self.conn.query( "FLUSH TABLES WITH READ LOCK" )
        
        mst = self.executesql( "SHOW MASTER STATUS" )[0]
        
        dodbs = mst['Binlog_Do_DB'].split(',') if mst['Binlog_Do_DB'] else None
        igndb = mst['Binlog_Ignore_DB'].split(',') if mst['Binlog_Ignore_DB'] else []
        
        dbs = self.executesql( "SHOW DATABASES" )
        
        dbs = [ db['Database'] for db in dbs ]
        dbs = [ db for db in dbs if ( (not dodbs) or db in dodbs ) and db not in igndb ]
        
        tbls = []
        for db in dbs :
            
            if not self.tablefilter((db,None)):
                continue
                
            tbls += [ ( db, tbs.values()[0] ) 
                      for tbs in self.executesql( "SHOW TABLES IN `%s`" % (db,) ) ]
        
        for tbl in tbls :
            
            if (not self.tablefilter(tbl)) or (not self.dumpfilter(tbl)) :
                continue
            
            rst = self.executesql( 'DESCRIBE `%s`.`%s`' % tbl )
            rst = [ (row['Field'], row['Type'].endswith('unsigned')) for row in rst ]
            
            cols = zip(*rst)
            self.tablest[tbl] = cols
            
            rst = self.executesqllarge( 
                "SELECT SQL_BIG_RESULT SQL_BUFFER_RESULT SQL_NO_CACHE "\
                "* FROM `%s`.`%s` " % tbl
            )
            
            for r in rst :
                yield None, tbl, r, None
        
        self.conn.query( "UNLOCK TABLES" )
        
        self.logname = mst['File']
        self.pos = mst['Position']
        
        yield (self.logname, self.pos, self.tablest), None, None, None
        
        return
    
    def tofetchrow( self, datas, q ):
        
        try :
            while(True):
                rs = datas.fetch_row( 500 )
                if len(rs) != 0 :
                    q.put(rs)
                else :
                    q.put(True)
                    return
                
        except Exception as e :
            q.put(False)
            q.put(e)
        
    def firstdumpbetter( self, nodump = False ):
        
        import MySQLdb
        import threading
        import Queue
        
        conn = MySQLdb.connect( **self.dbarg )
        
        locktable = False
        
        slv = CnL(conn).read( "SHOW SLAVE STATUS" )[0]
        if slv['Slave_IO_Running'] == 'YES' or slv['Slave_SQL_Running'] == 'YES':
            
            locktable = True
            CnL(conn).write( "FLUSH TABLES WITH READ LOCK" )
            
        
        mst = CnL(conn).read( "SHOW MASTER STATUS" )[0]
        
        dodbs = mst['Binlog_Do_DB'].split(',') if mst['Binlog_Do_DB'] else None
        igndb = mst['Binlog_Ignore_DB'].split(',') if mst['Binlog_Ignore_DB'] else []
        
        dbs = CnL(conn).getdatabases()
        
        dbs = [ db for db in dbs if ( (not dodbs) or db in dodbs ) and db not in igndb ]
        
        tbls = []
        for db in dbs :
            
            tbls += [ ( db, tb ) for tb in CnL(conn).gettables(db) ]
        
        self.run_pos = 0
        
        for tbl in tbls :
            
            if (not self.tablefilter(tbl)) or (not self.dumpfilter(tbl)) :
                continue
            
            for ii in range(3):
                try :
                    cols = [ col['Field'] for col in CnL(conn).getcols( tbl )]
                    break
                except :
                    if locktable == False :
                        conn = MySQLdb.connect( **self.dbarg )
            else :
                raise
            
            readsql = 'SELECT SQL_BIG_RESULT SQL_NO_CACHE %s FROM %s' % \
                               ( esql.formatcols(cols), esql.formattable(tbl) )
            
            conn.query( readsql )
            datas = conn.use_result()
            
            q = Queue.Queue(1000)
            
            fe = threading.Thread( target = self.tofetchrow, 
                                   args = ( datas, q ), 
                                   kwargs = {} 
                                 )
            
            fe.start()
            
            while( True ):
                
                rs = q.get()
                
                if rs == True :
                    break
                if rs == False :
                    raise q.get()
                
                for r in rs :
                    self.run_pos += 1
                    yield None, tbl, dict(zip(cols,r)), None
            
            fe.join()
        
        mst2 = CnL(conn).read( "SHOW MASTER STATUS" )[0]
        
        if mst['File'] != mst2['File'] or mst['Position'] != mst2['Position'] :
            raise Exception, ( 'lock table error', mst, mst2 )
        
        if locktable :
            CnL(conn).write( "UNLOCK TABLES" )
        
        self.logname = mst['File']
        self.pos = mst['Position']
        
        yield (self.logname, self.pos, self.tablest), None, None, None
        
        return
        
    def querybinlog( self ):
        
        arg = struct.pack('<L',self.pos)
        arg = arg + struct.pack('<H',0)
        arg = arg + struct.pack('<L',self.serverid)
        arg = arg + str(self.logname)
        
        self.conn._execute_command(self.COM_BINLOG_DUMP, arg)
        
        return
        
    def readloop( self, onconn=None, evyield=False ):
        
        #arg = struct.pack('<LHLs',self.pos,0,self.serverid,self.logname)
        
        #if (self.logname == None and self.pos == None) or self.tablest == None :
        #    for r in self.firstdump():
        #        yield r
        
        self.querybinlog()
        if onconn != None :
            onconn(self.conn, self.logname, self.pos, self.tablest)
            
        coltype = ()
        metadata = ()
        idt = {}
        
        self.run_pos = self.pos
        
        while(True):
            
            if evyield :
                yield EventWait
            
            try :
                r = self.ebp.read( 'binlog', self.conn.socket.makefile(), 
                                         extra_headers_length=0,
                                         coltype=coltype, 
                                         metadata=metadata,
                                         tst = self.tablest, idt=idt )
            except ezp.ConnectionError, e:
                self.conn = pymysql.connect( **self.dbarg )
                self.querybinlog()
                if onconn != None :
                    onconn(self.conn, self.logname, self.pos, self.tablest)
                continue
            
            try :
                self.run_pos = r['body']['content']['event']['header']['next_position']
            except :
                pass
            
            try :
                if 'error' in r['body']['content'] :
                    err = r['body']['content']['error']
                    raise MySQLBinLogError, (err['state'],err['code'],err['message'])
            except KeyError, e :
                pass
            
            try :
                coltype = r['body']['content']['event']['data']['table']['columns_type']
                metadata = r['body']['content']['event']['data']['table']['metadata']
                idt[r['body']['content']['event']['data']['table']['table_id']] = \
                    (r['body']['content']['event']['data']['table']['dbname'],
                     r['body']['content']['event']['data']['table']['tablename'])
            except KeyError, e :
                pass
            
            try :
                rot = r['body']['content']['event']['data']['rotate']
                self.logname, self.pos = rot['binlog'], rot['position']
                yield (self.logname, self.pos, self.tablest), None, None, None
                continue
            except KeyError, e :
                pass
            
            try :
                op, d = r['body']['content']['event']['data'].items()[0]
            except KeyError, e :
                yield None, None, None, None
                continue
            
            if op == 'query':
                
                _q = d['query'].strip().split()
                qtype = [ q.lower() for q in _q[:2] ]
                if q == ['create','table'] :
                    table = [ x.strip('`') for x in _q[3].split('.',1)]
                    table = [dbname] + table if dbname else table  
                    yield None, table[0], self.stablest, None
                elif q == ['alter','table'] :
                    table = [ x.strip('`') for x in _q[3].split('.',1)]
                    table = [dbname] + table if dbname else table  
                    yield None, table[0], self.stablest, None
                else :
                    yield None, None, None, None
                continue
            
            if op not in ('write_rows','update_rows','delete_rows') :
                yield None, None, None, None
                continue
                
            self.pos = r['body']['content']['event']['header']['next_position']
            t = idt[d['table_id']]
            
            if not self.tablefilter(t) :
                yield None, None, None, None
                continue
            
            if op == 'write_rows' :
                
                for x in d['value'][:-1] :
                    yield None, t, x, None
            
                yield (self.logname, self.pos, self.tablest), t, d['value'][-1], None
            
            elif op == 'update_rows' :
                
                v = zip( d['value'][::2], d['value'][1::2] )
                for b, a in v[:-1] :
                    yield None, t, a, b
                    
                yield (self.logname, self.pos, self.tablest), t, v[-1][1], v[-1][0]
                
            elif op == 'delete_rows' :
                
                for x in d['value'][:-1] :
                    yield None, t, x, None
            
                yield (self.logname, self.pos, self.tablest), t, None, d['value'][-1]
                
            else :
                
                yield None, None, None, None
        
        return
    

if __name__ == '__main__':
    
    import pprint
    
    # mysql -h10.210.74.143 -urepl test
    
    db = { 'host' : '10.210.74.143', 
           'port' : 3306, 
           'user' : 'repl',
         }

    erep = EasyReplication( db, ('mysql-bin.000002', 18724, None) )
    
    #erep = EasyReplication( db, None, tablefilter=( lambda x: ( x[0] == 'test' ) ), dbfilter=( lambda x: ( x != 'log' ) ) )
    
    for i in erep.readloop():
        pprint.pprint(i)
        print
        