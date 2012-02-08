import types
import pprint as pp

_commajoin = ", ".join
_id = id
_len = len
_type = type
_sorted = pp._sorted

class PrettyPrinter(pp.PrettyPrinter):
    
    colprinttype = set([ types.IntType, types.FloatType,
                         types.StringType, types.BooleanType, 
                         types.NoneType ])
    
    def _format(self, object, stream, indent, allowance, context, level):
        level = level + 1
        objid = _id(object)
        if objid in context:
            stream.write(_recursion(object))
            self._recursive = True
            self._readable = False
            return
        rep = self._repr(object, context, level - 1)
        typ = _type(object)
        sepLines = _len(rep) > (self._width - 1 - indent - allowance)
        write = stream.write

        if self._depth and level > self._depth:
            write(rep)
            return

        r = getattr(typ, "__repr__", None)
        if issubclass(typ, dict) and r is dict.__repr__:
            write('{')
            if self._indent_per_level > 1:
                write((self._indent_per_level - 1) * ' ')
            length = _len(object)
            if length:
                context[objid] = 1
                indent = indent + self._indent_per_level
                items = _sorted(object.items())
                key, ent = items[0]
                rep = self._repr(key, context, level)
                write(rep)
                write(': ')
                self._format(ent, stream, indent + _len(rep) + 2,
                              allowance + 1, context, level)
                if length > 1:
                    for key, ent in items[1:]:
                        rep = self._repr(key, context, level)
                        if sepLines:
                            write(',\n%s%s: ' % (' '*indent, rep))
                        else:
                            write(', %s: ' % rep)
                        self._format(ent, stream, indent + _len(rep) + 2,
                                      allowance + 1, context, level)
                indent = indent - self._indent_per_level
                del context[objid]
            write('}')
            return

        if ((issubclass(typ, list) and r is list.__repr__) or
            (issubclass(typ, tuple) and r is tuple.__repr__) or
            (issubclass(typ, set) and r is set.__repr__) or
            (issubclass(typ, frozenset) and r is frozenset.__repr__)
           ):
            length = _len(object)
            if issubclass(typ, list):
                write('[')
                endchar = ']'
            elif issubclass(typ, set):
                if not length:
                    write('set()')
                    return
                write('set([')
                endchar = '])'
                object = _sorted(object)
                indent += 4
            elif issubclass(typ, frozenset):
                if not length:
                    write('frozenset()')
                    return
                write('frozenset([')
                endchar = '])'
                object = _sorted(object)
                indent += 10
            else:
                write('(')
                endchar = ')'
            if self._indent_per_level > 1 and sepLines:
                write((self._indent_per_level - 1) * ' ')
            
            #print length, sepLines, [ type(i) for i in object ]
            
            if length and sepLines and \
                    all( type(i) in self.colprinttype for i in object):
                                          
                xobject = [ repr(i) for i in object ]
                maxlength = max( len(i) for i in xobject )
                rw = self._width - 1 - indent - allowance - 1
                cur = 0
                for x in xobject :
                    if cur >= rw :
                        write('\n' + ' '*(indent+1))
                        cur = 0
                    write(x)
                    cur += len(x)
                    write(', ')
                    cur += 2
            
            elif length:
                context[objid] = 1
                indent = indent + self._indent_per_level
                self._format(object[0], stream, indent, allowance + 1,
                             context, level)
                if length > 1:
                    for ent in object[1:]:
                        if sepLines:
                            write(',\n' + ' '*indent)
                        else:
                            write(', ')
                        self._format(ent, stream, indent,
                                      allowance + 1, context, level)
                indent = indent - self._indent_per_level
                del context[objid]
            if issubclass(typ, tuple) and length == 1:
                write(',')
            write(endchar)
            return

        write(rep)
    
def pprint(object, stream=None, indent=1, width=80, depth=None):
    """Pretty-print a Python object to a stream [default is sys.stdout]."""
    printer = PrettyPrinter(
        stream=stream, indent=indent, width=width, depth=depth)
    printer.pprint(object)

def pformat(object, indent=1, width=80, depth=None):
    """Format a Python object into a pretty-printed representation."""
    return PrettyPrinter(indent=indent, width=width, depth=depth).pformat(object)    
        
if __name__ == '__main__':
    
    pprint({'abc':list(range(100)),'def':list(range(5)),'ghi':'a\nb\n',
            'jkl':{'nop':[True,False,None]*10}
           })
    