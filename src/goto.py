
import re
import new


def goto( fcode ):
    
    lines = fcode.splitlines()
    
    lines = [ l for l in lines if l.strip() != '' ]
    
    lines = [ l if l.startswith(' ') elif 'if goto=="'+l.strip(':')+'"' for l in lines ]




if __name__ == "__main__" :
    
    
    c = """
    print "hello world"
    i = 0
loop:
    print i
    i += 1
    if i < 10 :
        goto end
    goto loop
end:
    pass
    """
    
    f = goto(c):
    
    f()