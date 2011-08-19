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
    
    if type(v) == datetime.datetime :
        return v.strftime('%Y-%m-%d %H:%M:%S')
    
    return "'"+pymysql.escape_string(str(v))+"'"

def formatcond( k, v ):
    
    if v is None :
        return '`' + k + '` is NULL'
    
    return '`' + k + '` = ' + formatvalue)v)

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
    
    def gets( self, tb, cols=None, where=None, order=None, reverse=False ):
        
        if type(tb) in (types.TupleType, types.ListType ):
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)
        
        if cols == all :
            cs = self.cols
        elif cols is None :
            cs = self.defaultcols
        else :
            cs = [ c for c in cols if c in self.cols ]
                
        cs = ', '.join( c.join(['`','`']) for c in cs )
        
        if where is None :
            where = ''
        else :
            where = ' WHERE ' + ' AND '.join( [ formatcond(k,v) for k, v in where.items() if k in self.cols ] )
        
        return self.read( 'SELECT %s from %s%s'  % ( cs, tb, where ) )
    
    def puts( self, tb, datas, ignore=False, ondupupdate=False ):
        
        if datas == [] :
            return
        
        if type(tb) in (types.TupleType, types.ListType ):
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)
        
        ks = set([ k for d in datas for k in d.keys() ])
        vss = [ [ d.get(k,None) for k in ks ] for d in datas ]
        
        ks = ', '.join( c.join(['`','`']) for k in ks )
        vss = [ '('+', '.join( formatvalue(v) for v in vs )+')' for vs in vss ]
        vss = ', '.join(vss)
        
        if ignore :
            verb = "INSERT IGNORE"
        else :
            verb = "INSERT"
        
        sql = "%s INTO %s (%s) VALUES %s" % ( verb, tb, ks, vss )
        
        return self.write(sql)
    
    def put( self, tb, data, *args, **kwargs ):
        
        return self.puts( tb, [data], *args, **kwargs )
    
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
            
            except pymysql.OperationalError, e:
                if e.args[0] == 2006 :
                    self.reconnect()
                else :
                    raise
            except pymysql.ProgrammingError, e :
                e.args = tuple( list(e.args)+[sql,] )
                raise
            
            break
            
        else :
            raise
        
        return [ dict(zip(dsc,r)) for r in rst ]
            
    def write( self, sql ):
        
        for i in range(self.retrytimes):
            try :
                self.conn.query( sql )
            except pymysql.OperationalError, e:
                if e.args[0] == 2006 :
                    self.reconnect()
                else :
                    raise
            except pymysql.ProgrammingError, e :
                e.args = tuple( list(e.args)+[sql,] )
                raise
            
            break
            
        else :
            raise
        
        return


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
        
        datas = [ dict( ( k, v ) for k, v in data.items() if k in self.cols )
                  for data in datas
                ]
        
        return self.conn.puts( self.name, datas, *args, **kwargs )
    
    def put( self, data, *args, **kwargs )

        data = [ ( k, v ) for k, v in data.items() if k in self.cols ]
        
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
    
    
    db = { 'host' : 'localhost', 
           'port' : 3306, 
           'user' : 'root',
           'passwd' : '',
           'db' : 'test'
         }
    
    edb = Database(db)
    
    print edb.project.gets(cols=['ProjectID','Project'])
    