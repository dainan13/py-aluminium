=========================
 Easysql
=========================




 Designs
=========================

the aim is a MySql client which without writing sql request. all operate by
pass though datastructures.

an operate in commen code fasion ::
    
    conn = Connection( host='127.0.1', port=3306, db='test_db' )
    
    # ...
    
    conn.query( 'SElECT `col1`, `col2` FROM `%s` WHERE `ref` =%d ' \
                    % ( tablename, 0 )
              )
    
    rst = conn.store_result()
    
    rst = [ dict(zip(keys, row)) for row in rst.fetch_row(rst.num_rows()) ]
    
    conn.close()
    
    # ...

    
here is two problem in code, one is mistake and syntax error, another is
working hard if the database's construction has changed. so, I want a smart
libuary to help me to glue the datastructure and database's construction.
it may be like this ::
    
    table << {'attr':'1'}    # insert
    table[{'attr':1}]        # select
    del table[{'attr':1}]    # delete
    

then, the libuary need some property. the first is to separate the operation
with single object or multi objects.

for example ::

    array = [1,2,3]
    table = Table()
    
    array[x]           # raise if x index out of array
    table[d]           # raise if d conditions not found
    
    array[x:y]         # [] if x and y index out of array 
    table[::d]         # [] if d conditions not found


the second property is data translate.

for example ::
    
    table = Table()
    table.setdatabuilder( 'attr', lambda x = str(x), lambda x = eval(x) )
    
    table << {'attr':True} << {'attr':False} << {'attr':None}


the third property is subdatabase and subtable's support.

for example ::

    >>> subtable1 = Table()
    >>> subtable2 = Table()
    
    >>> table = subtable1 & subtable2
    >>> table.setsplitter( lambda x : [0, 1] if 'a' not in x else \
                                      [0,] if x['a'] > 0 else [1,] )
    
    >>> table << {'a':1, 'b':'hello', 'c':1} << {'a':-1, 'b':'world', 'c':1}
    
    >>> subtable1[{'a':1}]
    {'a':1, 'b':'hello'}
    >>> subtable2[{'a':-1}]
    {'a':-1, 'b':'world'}
    
    >>> table[::{'c':1}]
    [{'a':1, 'b':'hello'}, {'a':-1, 'b':'world'}]


 Basic Operate
-------------------------

===============  ============================================================================   ==================================================
operate           examples                                                                       return
===============  ============================================================================   ==================================================
insert(single)    table << {'attr':'inserted'}                                                   self, raise on duplicate
                  lastid = table.append( {'attr':'inserted'} )                                   lastid or None(duplicate)
insert(multi)     table << [{'attr':'inserted'},]                                                self, raise on duplicate
                  table += [{'attr':'inserted'},]                                                -, raise on duplicate
                  table.expend( [{'attr':'inserted'},] )                                         success number
insert(ondup)     lastid = table.append( {'attr':'inserted'}, ondup = {'attr':'updated'} )       lastid or -lastid(duplicate)
select(single)    table[{'attr':1}]                                                              item, raise on not found
                  table['attr1','attr2']                                                         item's sub dict, raise on not found
                  table.get( {'ID':1} )                                                          item, raise on not found
                  table.get( {'ID':1}, default=None, keys=[] )                                   None or the item
                  a = {'ID':1} ; table >> a                                                      fill item to a and returned, raise on not found
select(multi)     table[::{'attr':1}]                                                            [] or items which attr eq 1
                  table['attr1','attr2',:50:]                                                    [] or list of item's sub dict, max 50 items
                  table.gets( {'attr':1}, keys=[], limit=n, offset = p )                         [] or list of item
update(single)    table[{'attr1':1}] = {'attr2':'updated'}                                       -, raise on not found
                  table['attr1'] = {'attr1':1, 'attr2':'updated'}                                -, raise on not found
                  table.set( {'ID':1}, {'attr':'updated'} )                                      True or False
update(multi)     table[::{'attr1':1}] = {'attr2':'updated'}                                     -
                  table['attr1',::] = {'attr1':1, 'attr2':'updated'}                             -
                  table.sets( {'ID':1}, {'attr':'updated'}, limit=n )                            success number
replace(single)   table <<= {'attr':'inserted'}                                                  -
                  lastid = table.load( {'attr':'replaced'} )                                     lastid
replace(multi)    table <<= [{'attr':'inserted'},]                                               -
                  table.loads( [{'attr':'replaced'},] )                                          success number
delete(single)    del table[{'attr1':1}]                                                         -, raise on not found
                  table.remove({'attr1':1})                                                      True or False
delete(multi)     del table[::{'attr1':1}]                                                       -
                  table.removes({'attr1':1})                                                     success number
===============  ============================================================================   ==================================================




 More Operate
-------------------------

===============  =============================
operate           example
===============  =============================
turncate          table.clear()
keys              table.keys()
has_key           col in table
===============  =============================


 Advance Operate
-------------------------

==========  ===========================================================  ==========================
object       example                                                      tails
==========  ===========================================================  ==========================
this         table[{'attr':1}] = {'ref':this('ref')+1}                    colume ref += 1
             table[{'attr':1}] = {'attr3':this('attr1')+this('attr2')}    attr3 = attr1 + attr2
func         table << { 'attr':1, func['HEX']('A0') }
raw          table[{'attr':raw('<3')}]
mix          table[{'attr':mix(raw('>3'),raw('<5'))}]
count        table[count]                                                 count the table
             table[count,{'attr1':1}]                                     count items which attr=1
SQL/holder   SQL(table)[{'attr':1}]                                       parse to sql
             g = SQL(table)[{'attr':holder()}]; print g ; g % (x,)
             SQL(table)[{'attr':holder('a')}] % {'a':x}
complex      table[{'attr2':SQL(table)[{'attr1':1}]['attr2']}]
==========  ===========================================================  ==========================