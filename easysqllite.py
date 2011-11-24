import types
import struct
import pymysql
import datetime

class EasySqlLiteException( Exception ):
    pass

def formatcols( cols ):
    return ','.join( ('`%s`' % (c) if c is not None else 'NULL') for c in cols )

def formattable( tb ):

    if type(tb) in (types.TupleType, types.ListType ):
        tb = '`%s`.`%s`' % tuple(tb)

    else :
        tb = '`%s`' % (tb,)

    return tb

def formatvalue( v ):

    if v is None :
        return 'NULL'

    if type(v) in (types.IntType,types.LongType,types.FloatType):
        return str(v)

    if type(v) == datetime.datetime :
        return pymysql.escape_string( v.strftime('%Y-%m-%d %H:%M:%S') )

    return pymysql.escape_string((v))

def formatcond( k, v ):

    if v is None :
        return '`' + k + '` IS NULL'

    if type(v) is types.TupleType and len(v) == 2 :

        left = ( '`' + k + '` >= ' + formatvalue(v[0]) ) if v[0] else 'TRUE'
        right = ( '`' + k + '` < ' + formatvalue(v[1]) ) if v[1] else 'TRUE'

        return  left + ' AND ' + right


    return '`' + k + '` = ' + formatvalue(v)

def makecond( condition ):
    
    if type(condition) in (types.TupleType, types.ListType ):
        condition = [' '.join((col.join(['`', '`']), oper, formatvalue(val))) for col, oper, val in condition]
        
    elif type(condition) == types.DictType:
        condition = [ formatcond(k,v) for k, v in condition.items() ]
    
    else :
        raise EasySqlLiteException, 'Can not format condition'
    
    return " AND ".join(condition)


class ConnLite( object ):

    def __init__( self, conn ):

        self.conn = conn


    def read( self, sql ):

        cur = self.conn.cursor()
        cur.execute( sql )
        dsc = cur.description
        dsc = [ d[0] for d in dsc ]

        rst = cur.fetchall()
        cur.close()

        return [ dict(zip(dsc,r)) for r in rst ]
        
    def readlarge( self, sql ):

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

    def query( self, sql, _unused ):

        return self.conn.query( sql )

    write = query

    def gets( self, tb, cols=None, where=None, order=None, group=None, reverse=False, limit=None ):

        tb = formattable( tb )

        if cols == all :
            cs = '*'
        elif cols is None :
            cs = '*'
        else :
            cs = [ c for c in cols if c in cols ]

            cs = ', '.join( c.join(['`','`']) for c in cs )

        if where is None or where == {} :
            where = ''
        else :
            #where = ' WHERE ' + ' AND '.join( [ formatcond(k,v) for k, v in where.items() ] )
            where = ' WHERE ' + makecond(where)

        if order is None :
            order = ''
        else :
            order = [o.join(['`', '`']) for o in order]
            if reverse is False:
                reverse = ''
            elif reverse is True:
                reverse = ' DESC'
            order = ' ORDER BY %s%s' % (','.join(order),reverse)

        if group is None :
            group = ''
        else :
            group = ' GROUP BY %s' % ','.join(group)

        if limit is None :
            limit = ''
        else :
            limit = ' LIMIT %s' %str(limit)

        #print 'SELECT %s FROM %s%s%s%s%s'  % ( cs, tb, where, group, order, limit )

        return self.read( 'SELECT %s FROM %s%s%s%s%s'  % ( cs, tb, where, group, order, limit  ) )

    def puts( self, tb, datas, ignore=False, replace=False, ondupupdate=False ):
        if datas == [] :
            return
        tb = formattable( tb )

        ks = set([ k for d in datas for k in d.keys() ])
        vss = [ [ d.get(k,None) for k in ks ] for d in datas ]
        #print ks,vss
        ks = ', '.join( k.join(['`','`']) for k in ks )
        vss = [ '('+', '.join( formatvalue(v) for v in vs )+')' for vs in vss ]
        vss = ', '.join(vss)
        #print vss
        if replace :
            verb = "REPLACE"
        elif ignore :
            verb = "INSERT IGNORE"
        else :
            verb = "INSERT"

        sql = "%s INTO %s (%s) VALUES %s" % ( verb, tb, ks, vss )

        return self.write( sql, replace or ignore )

    def put( self, tb, data, *args, **kwargs ):

        return self.puts( tb, data, *args, **kwargs )
        
    def update( self, tb, data, where=None ):
        if data == [] :
            return
        tb = formattable( tb )
            
        kvs = ', '.join( '`%s` = %s' % ( k, formatvalue(v) ) for k, v in data.items() )
        
        sql = "UPDATE %s SET %s" % ( tb, kvs, )
        
        if where:
            sql = "%s WHERE %s" % ( sql, makecond(where), )
        
        print sql
        return self.write( sql, )
        
    def delete( self, tb, where=None ):
        
        if type(tb) in (types.TupleType, types.ListType ):
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)
            
        sql = "DELETE FROM %s" %tb
        
        if where:
            sql = "%s WHERE %s" % ( sql, makecond(where), )
            
        print sql

        self.write( sql, True )

    def getdatabases( self ):

        dbs = self.read( "SHOW DATABASES" )

        return [ db['Database'] for db in dbs ]

    def gettables( self, db=None ):

        if db == None :
            db = ''
        else :
            db = ' IN `%s`' % (db,)

        r = self.read( "SHOW FULL TABLES%s WHERE table_type='BASE TABLE'" % (db,))

        if r == [] :
            return []

        k = [ k for k in r[0].keys() if k.startswith('Tables_in_') ][0]

        return [ tb[k] for tb in r ]

    def getcols( self, tb ):

        tb = formattable( tb )

        return self.read( "DESCRIBE " + tb )
        
    def getMasterStatus( self, ):
        
        return self.read( "SHOW MASTER STATUS" )
        
    def getUptime( self, ):

        return self.read( "SHOW STATUS LIKE 'Uptime'" )
        
    def querybinlog( self, pos, serverid, logname, com_binlog_dump ):
        
        arg = struct.pack( '<L', pos )
        arg = arg + struct.pack( '<H', 0 )
        arg = arg + struct.pack( '<L', serverid )
        arg = arg + str( logname )
        
        self.conn._execute_command( com_binlog_dump, arg )
        
        return

class Connection( ConnLite ):

    def __init__( self, dbopt ):

        self.dbopt = dbopt
        self.conn = pymysql.connect( **self.dbopt )
        self.conn.query('SET AUTOCOMMIT = 1')
        self.retrytimes = 5

        return

    def reconnect( self ):
        for i in range(5):
            try :
                self.conn = pymysql.connect( **self.dbopt )
                self.conn.query('SET AUTOCOMMIT = 1')
                return
            except pymysql.OperationalError, e :
                continue
        raise
            

    def read( self, sql ):
        
        #print 'ESQL, read>', sql

        for i in range( self.retrytimes ):
            try :

                cur = self.conn.cursor()
                cur.execute( sql )
                dsc = cur.description
                dsc = [ d[0] for d in dsc ]

                rst = cur.fetchall()
                cur.close()

                break

            except pymysql.OperationalError, e:
                if e.args[0] in ( 2006, 2013 ) :
                    self.reconnect()
                else :
                    raise
            except pymysql.ProgrammingError, e :
                e.args = tuple( list(e.args)+[sql,] )
                raise

        else :
            raise

        return [ dict(zip(dsc,r)) for r in rst ]

    def write( self, sql, retry=False ):
        
        #print sql
        
        affectRows = 0
        self.reconnect()
        oe_retry = ( 2006, 2013 ) if retry else ( 2006, )

        for i in range(self.retrytimes):
            try :
                #print i, '\n'
                affectRows = self.conn.query( sql )
                #self.conn.query("commit")
                break

            except pymysql.OperationalError, e:
                if e.args[0] in oe_retry :
                    self.reconnect()
                else :
                    raise
            except pymysql.ProgrammingError, e :
                e.args = tuple( list(e.args)+[sql,] )
                raise

            except:
                raise
        else :
            raise
        
        #print 'process ok'
        
        return affectRows


class Table( object ):

    def __init__( self, name, conn, cols ):

        self.name = name
        self.conn = conn

        self.cols = set(cols)
        self.defaultcols = [ c for c in self.cols if not c.startswith('_') ]

        return

    def gets( self, cols=None, *args, **kwargs ):

        if cols == all :
            cs = self.cols
        elif cols is None :
            cs = self.defaultcols
        else :
            cs = [ c for c in cols if c in self.cols ]

        return self.conn.gets( self.name, cs, *args, **kwargs )

    def puts( self, datas, *args, **kwargs  ):
        datas = [ dict( ( k, v ) for k, v in data.items() if k in self.cols) for data in datas  ]
        return self.conn.puts( self.name, datas, *args, **kwargs )

    def put( self, data, *args, **kwargs ):

        data = [ dict(( k, v ) for k, v in data.items() if k in self.cols) ]

        return self.conn.put( self.name, data, *args, **kwargs )

    def update( self, data, *args, **kwargs ):
        
        data = [ dict(( k, v ) for k, v in data.items() if k in self.cols) ]
        
        return self.conn.update( self.name, data, *args, **kwargs )
        
    def delete( self, *args, **kwargs ):
        
        return self.conn.delete( self.name, *args, **kwargs )

class Database( object ):

    def __init__( self, dbopt ):

        self.db = dbopt['db']

        self.conn = Connection(dbopt)

        tbs = self.conn.gettables()

        tbdefs = [ [ c['Field'] for c in self.conn.getcols(tb) ]
                   for tb in tbs ]

        tbs = dict( ( tb.lower(), Table( tb, self.conn, tbdef ) )
                    for tb, tbdef in zip( tbs, tbdefs ) )

        self.tables = tbs

        return

    def __getattr__( self, key ):

        key = key.lower()

        if key not in self.tables :
            raise KeyError, 'not has table named `%s`' %(key,)

        return self.tables[key]

if __name__ == '__main__' :


    db = { 'host' : '127.0.0.1',
           'port' : 3377,
           'user' : 'usr',
           'passwd' : 'pswd',
           'db' : 'yourdb'
         }

    edb = Database(db)

    #print edb.stt_cpuall_fivemin.gets(['AN','coreid','ctime','iowait'],where = {'ctime':(None,'2011-08-22 00:00:00')},order = ['ctime'],reverse = True,limit = '10')
    #print edb.table_info.puts([{'table_name':'tname'},{'table_name':'tname2'}])
    #print edb.conn.getdatabases()
    print edb.table_info.put({'table_name':'tname'})
    #print edb.conn.getcols('stt_cpuall_fivemin');
