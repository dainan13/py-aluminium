import easyprotocol as ezp
import pymysql
import struct
import datetime

class EasyRepError(Exception):
    pass

class UnkownDBArgs(EasyRepError):
    pass

class UnknowTableDefine(EasyRepError):
    pass

class UnknowColumnType(EasyRepError):
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
    
    def __init__( self ):
        
        self.name = 'rows'
        self.cname = 'rows'
        
        self.identifiable = True
        self.stretch = True
        
        self.variables = []
        
        self.sqlquery = None
        
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
        
    
    def read( self, namespace, fp, lens, args ):
        
        x = fp.read(lens)

        l = 0
        r = []

        columns_count, coltypes, tst, idt, tid = args
        
        tname = idt.get(tid, None)
        
        if tname == None :
            raise Exception, ('table id error', tid)
        
        cols = tst.get(tname, None)
        
        if not cols :
            
            if not self.sqlquery :
                raise UnknowTableDefine, '.'.join(tname)
            
            try :
                rst = self.sqlquery( 'DESCRIBE `%s`.`%s`' % tname )
            except UnkownDBArgs:
                raise UnknowTableDefine, '.'.join(tname)
            
            rst = [ (row['Field'], row['Type'].endswith('unsigned')) for row in rst ]
            
            cols = zip(*rst)
            tst[tname] = cols
            
        fieldnames, cola = cols
        
        if columns_count != len(coltypes) :
            raise Exception, ('columns error', columns_count, coltypes)

        while l < lens :
            
            isnull, l = self.readbit( x, l, columns_count )
            cols = zip( coltypes, isnull, cola )
            
            rr = []
            
            for coltype, isnull, ca in cols :
                
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
                    rr.append( datetime.datetime.strptime(str(_r),'%Y%m%d%H%M%S') )
                    d = str(self.readint(fp,8))
                elif coltype == 15 : # varchar
                    _r, l = self.readint(x,l,2)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 249 : # tiny blob / text
                    _r, l = self.readint(x,l,1)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 250 : # medium blob / text
                    _r, l = self.readint(x,l,3)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 251 : # long blob / text
                    _r, l = self.readint(x,l,4)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 252 : # blob / text
                    _r, l = self.readint(x,l,2)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 253 : # varbinary
                    _r, l = self.readint(x,l,2)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                elif coltype == 254 : # binary
                    _r, l = self.readint(x,l,1)
                    _r, l = self.readchar(x,l,_r)
                    rr.append( _r )
                else :
                    raise UnknowColumnType, ('unkown column type',coltype)
            
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
        


class EasyReplication(object):
    
    #dbargsort = ('host', 'port', 'user', 'passwd', 'db',)
    
    COM_BINLOG_DUMP = 18
    
    ebp = ezp.EasyBinaryProtocol()
    ebp.buildintypes.append(RowType())
    ebp.buildintypes.append(PACKINTType())
    ebp.namespaces = dict( (bt.name, bt) for bt in ebp.buildintypes )
    ebp.parsefile( 'replication.protocol' )
    
    def __init__( self, logname, pos, db, 
                        tablefilter=None, dbfilter=None,
                        autodesc=False ):
        
        self.conn = pymysql.connect( **db )
        self.dbarg = db
        self.serverid = 1
        self.logname = logname
        self.pos = pos
        self.tablefilter = tablefilter or ( lambda x : True )
        self.dbfilter = dbfilter or ( lambda x : True )
        
        if autodesc :
            self.ebp.namespaces['rows'].sqlquery = self.executesqlone
        
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
        
    def firstdump( self ):
        
        self.conn.query( "FLUSH TABLES WITH READ LOCK" )
        
        mst = self.executesql( "SHOW MASTER STATUS" )[0]
        
        dodbs = mst['Binlog_Do_DB'].split(',') if mst['Binlog_Do_DB'] else None
        igndb = mst['Binlog_Ignore_DB'].split(',') if mst['Binlog_Ignore_DB'] else []
        
        dbs = self.executesql( "SHOW DATABASES" )
        
        dbs = [ db['Database'] for db in dbs ]
        dbs = [ db for db in dbs if ( (not dodbs) or db in dodbs ) and db not in igndb ]
        
        tbls = []
        for db in dbs :
            
            if not self.dbfilter(db):
                continue
                
            tbls += [ ( db, tbs.values()[0] ) 
                      for tbs in self.executesql( "SHOW TABLES IN `%s`" % (db,) ) ]
        
        for tbl in tbls :
            
            if not self.tablefilter(tbl):
                continue
            
            rst = self.executesqllarge( 
                "SELECT SQL_BIG_RESULT SQL_BUFFER_RESULT SQL_NO_CACHE "\
                "* FROM `%s`.`%s` " % tbl
            )
            
            for r in rst :
                yield None, tbl, r, None
        
        self.conn.query( "UNLOCK TABLES" )
        
        self.logname = mst['File']
        self.pos = mst['Position']
        
        yield (self.logname, self.pos), None, None, None
        
        return
        
    def readloop( self ):
        
        #arg = struct.pack('<LHLs',self.pos,0,self.serverid,self.logname)
        
        if self.logname == None and self.pos == None :
            for r in self.firstdump():
                yield r
        
        arg = struct.pack('<L',self.pos)
        arg = arg + struct.pack('<H',0)
        arg = arg + struct.pack('<L',self.serverid)
        arg = arg + str(self.logname)
        
        self.conn._execute_command(self.COM_BINLOG_DUMP, arg)
        
        coltype = ()
        tst = {}
        idt = {}
        
        while(True):
            
            r = self.ebp.read( 'binlog', self.conn.socket.makefile(), 
                                         extra_headers_length=0,
                                         coltype=coltype, 
                                         tst = tst, idt=idt )
            try :
                coltype = r['body']['content']['event']['data']['table']['columns_type']
                idt[r['body']['content']['event']['data']['table']['table_id']] = \
                    (r['body']['content']['event']['data']['table']['dbname'],
                     r['body']['content']['event']['data']['table']['tablename'])
            except KeyError, e :
                pass
            
            try :
                rot = r['body']['content']['event']['data']['rotate']
                self.logname, self.pos = rot['binlog'], rot['position']
                yield (self.logname, self.pos), None, None, None
                continue
            except KeyError, e :
                pass
            
            try :
                op, d = r['body']['content']['event']['data'].items()[0]
            except KeyError, e :
                yield None, None, None, None
                continue
            
            if op not in ('write_row','update_rows','delete_row') :
                yield None, None, None, None
                continue
                
            self.pos = r['body']['content']['event']['header']['next_position']
            t = idt[d['table_id']]
            
            if not self.tablefilter(t) :
                yield None, None, None, None
                continue
            
            if op == 'write_row' :
                
                for x in d['value'][:-1] :
                    yield None, t, x, None
            
                yield (self.logname, self.pos), t, d['value'][-1], None
            
            elif op == 'update_rows' :
                
                v = zip( d['value'][::2], d['value'][1::2] )
                for a, b in v[:-1] :
                    yield None, t, a, b
                    
                yield (self.logname, self.pos), t, v[-1][0], v[-1][1]
                
            elif op == 'delete_row' :
                
                for x in d['value'][:-1] :
                    yield None, t, x, None
            
                yield (self.logname, self.pos), t, None, d['value'][-1]
                
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
    
    #erep = EasyReplication( 'mysql-bin.000080', 556, db )
    #erep = EasyReplication( 'mysql-bin.000080', 0, db )
    #erep = EasyReplication( 'mysql-bin.000080', 187, db )
    #erep = EasyReplication( 'mysql-bin.000080', 2996, db, autodesc=True )
    erep = EasyReplication( None, None, db, tablefilter=( lambda x: ( x[0] == 'test' ) ), dbfilter=( lambda x: ( x != 'log' ) ), autodesc=True )
    
    for i in erep.readloop():
        pprint.pprint(i)
        print
        