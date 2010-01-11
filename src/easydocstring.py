
import types

class Table( object ):
    
    def __init__( self, columns, table ):
        
        self.columns = dict([ ( c, i ) for i, c in enumerate(columns) ])
        
        self.index = {}
        
        self.values
        
        return
    
    def __getitem__( self, i ):
        '''
        t[1]
        t['Name':'Cover']
        t[:,'Machine']
        t[5:7,'Machine']
        t['Name':'Cover',::'Machine']
        t[5:7,6:9]
        '''
        
        if len(i) == 1 :
            if type(i) == types.SliceType :
                if type( i.start ) == types.IntType :
                    rowindex = i
                else :
                    c = self.columns[i.start]
                    rs = [ i for i, r in enumerate(self.values)
                           if r[c] == i.stop ]
                    if len(rs) > 1 :
                        raise IndexError, ( 'Multi Rows "%s"="%s" ' % (i.start,i.stop) )+ 'Line:' + ','.join(rs) 
                    elif len(rs) == 0 :
                        raise IndexError, '"%s" Not Found' % (i.start,i.stop)
        
        
        return
    
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

    
