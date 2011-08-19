import types
import pymysql
#import MySQLdb as pymysql

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
        
        self.conn.query( sql )
        
        return self.conn.commit()
        
    write = query
    
    def get( self, tb, cols=None, where=None ):
        
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
            where = ' WHERE ' + ' AND '.join( [ self.makecolcond(k,v) for k, v in where.items() if k in self.cols ] )
        
        return self.read( 'SELECT %s from %s%s'  % ( cs, tb, where ) )
        
    def add( self, tb, data, ignore=False, ondupupdate=False ):
        
        if type(tb) in (types.TupleType, types.ListType ):
            tb = '`%s`.`%s`' % tuple(tb)
        else :
            tb = '`%s`' % (tb,)
            
        data = [ ( k, v ) for k, v in data.items() if k in self.cols ]
        ks, vs = zip(*data)
        
        ks = ', '.join( c.join(['`','`']) for k in ks )
        vs = ', '.join( str(v).join(["'","'"]) for v in vs )
        
        if ignore :
            verb = "INSERT IGNORE"
        else :
            verb = "INSERT"
        
        sql = "%s INTO %s (%s) VALUES (%s)" % ( verb, tb, ks, vs )
        
        return self.write(sql)
    
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
    
class Connection( object ):
    
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
                self.conn.commit()
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
        
    def makecolcond( self, k, v ):
        
        if v is None :
            return '`%s` is NULL' % (k,)
        else :
            return "`%s`='%s'" % (k, str(v)) 

    def read( self, cols=None, where=None ):
        
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
            where = ' WHERE ' + ' AND '.join( [ self.makecolcond(k,v) for k, v in where.items() if k in self.cols ] )
        
        return self.conn.read( 'SELECT %s from `%s`%s'  % (cs,self.name,where) )
        
    def add( self, data, ignore=False, ondupupdate=False ):
        
        data = [ ( k, v ) for k, v in data.items() if k in self.cols ]
        ks, vs = zip(*data)
        
        ks = ', '.join( k.join(['`','`']) for k in ks )
        vs = ', '.join( str(v).join(["'","'"]) for v in vs )
        
        if ignore :
            verb = "INSERT IGNORE"
        else :
            verb = "INSERT"
        
        sql = "%s INTO `%s` (%s) VALUES (%s)" % ( verb, self.name, ks, vs )
        
        return self.conn.write(sql)
    
class Database( object ):
    
    def __init__( self, dbopt ):
        
        self.db = dbopt['db']
        
        self.conn = Connection(dbopt)
        
        tbs = self.conn.read("SHOW FULL TABLES WHERE table_type='BASE TABLE'")
        tbs = [ tb['Tables_in_'+self.db] for tb in tbs ]
        
        tbs = dict( ( tb.lower(), Table(tb, self.conn, self.gettablecols(tb)) ) 
                    for tb in tbs )
        
        self.tables = tbs
        
        return
    
    def gettablecols( self, tb ):
        
        return [ col['Field'] for col in self.conn.read('DESCRIBE `'+tb+'`') ]

    def __getattr__( self, key ):
        
        key = key.lower()
        
        if key not in self.tables :
            raise KeyError, 'not has table named `%s`' %(key,)
        
        return self.tables[key]
        
if __name__ == '__main__' :
    
    
    db = { 'host' : '10.29.10.194', 
           'port' : 3377, 
           'user' : 'SinaStore_r',
           'passwd' : '4eb871692703122b',
           'db' : 'SinaStore'
         }
    
    edb = Database(db)
    
    print edb.project.read(cols=['ProjectID','Project'])
    