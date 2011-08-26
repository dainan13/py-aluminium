import types
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
        return v.strftime('%Y-%m-%d %H:%M:%S')

    return pymysql.escape_string((v))

def formatcond( k, v ):

    if v is None :
        return '`' + k + '` IS NULL'

    if type(v) is types.TupleType and len(v) == 2 :

        left = ( '`' + k + '` >= ' + formatvalue(v[0]) ) if v[0] else 'TRUE'
        right = ( '`' + k + '` < ' + formatvalue(v[1]) ) if v[1] else 'TRUE'

        return  left + ' AND ' + right


    return '`' + k + '` = ' + formatvalue(v)

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

    def query( self, sql ):

        return self.conn.query( sql )

    write = query

    def gets( self, tb, cols=None, where=None, order=None, group=None, reverse=False, limit=None ):

        if type(tb) in (types.TupleType, types.ListType ):
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)

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
            where = ' WHERE ' + ' AND '.join( [ formatcond(k,v) for k, v in where.items() ] )

        if order is None :
            order = ''
        else :
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

    def puts( self, tb, datas, ignore=False, ondupupdate=False ):
        if datas == [] :
            return
        if type(tb) in (types.TupleType, types.ListType ):
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)

        ks = set([ k for d in datas for k in d.keys() ])
        vss = [ [ d.get(k,None) for k in ks ] for d in datas ]
        #print ks,vss
        ks = ', '.join( k.join(['`','`']) for k in ks )
        vss = [ '('+', '.join( formatvalue(v) for v in vs )+')' for vs in vss ]
        vss = ', '.join(vss)
        #print vss
        if ignore :
            verb = "INSERT IGNORE"
        else :
            verb = "INSERT"

        sql = "%s INTO %s (%s) VALUES %s" % ( verb, tb, ks, vss )

        return self.write( sql,ignore )

    def put( self, tb, data, *args, **kwargs ):

        return self.puts( tb, data, *args, **kwargs )

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

        if type(tb) in (types.TupleType, types.ListType ) :
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)

        return self.read( "DESCRIBE " + tb )


class Connection( ConnLite ):

    def __init__( self, dbopt ):

        self.dbopt = dbopt
        self.conn = pymysql.connect( **self.dbopt )
        self.retrytimes = 5

        return

    def reconnect( self ):
        self.conn = pymysql.connect( **self.dbopt )

    def read( self, sql ):

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

    def write( self, sql, ignore=False ):
        self.reconnect()
        oe_retry = ( 2006, 2013 ) if ignore else ( 2006, )

        for i in range(self.retrytimes):
            try :
                self.conn.query( sql )
                self.conn.query("commit")
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
        return "Insert OK!"


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


    db = { 'host' : 'm3950i.orion.grid.sina.com.cn',
           'port' : 3950,
           'user' : 'sinastore',
           'passwd' : 'f3u4w8n7b3h',
           'db' : 'SinaStoreTJ'
         }

    edb = Database(db)

    #print edb.stt_cpuall_fivemin.gets(['AN','coreid','ctime','iowait'],where = {'ctime':(None,'2011-08-22 00:00:00')},order = ['ctime'],reverse = True,limit = '10')
    #print edb.table_info.puts([{'table_name':'tname'},{'table_name':'tname2'}])
    #print edb.conn.getdatabases()
    print edb.table_info.put({'table_name':'tname'})
    #print edb.conn.getcols('stt_cpuall_fivemin');
