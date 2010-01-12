
import types

def getkeys( input ):
    
    if type(input) == types.DictType :
        return input.keys()
        
    elif type(input) in ( types.TupleType, types.ListType )\
         and all( [ type(i) == types.DictType for i in input ] ):
        
        return list( set( sum( [ i.keys() for i in input ], [] ) ) )
        
    return []
    
def getcols( input ):
    
    return []