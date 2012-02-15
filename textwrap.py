# -*- coding: utf-8 -*-

initials = u'([{<$'
           u'￥【“‘《'
           
tails = u'!%)]:;>?,.'
        u'·！…）】、：；”’》，。？'
           
letter = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
         'abcdefghijklmnopqrstuvwxyz'
         '0123456789'
         '~`@#^&*_-+=|\\"\'/'

def split_word( s ):    
    
    r = []
    
    onword = True
    innerspace = False
    wordpos = 0
    spacepos = 0
    
    for i, c in enumerate(s) :
        
        if onword :
            
            if c in letter or c in tails :
                spacepos = i
                innerspace = False
                continue
                
            elif c in initials :
                spacepos = i
                innerspace = True
                continue
                
            elif c == ' ' :
                spacepos = i
                if not innerspace :
                    onword = False
                continue
                
            elif c in '\t\r\n' :
                spacepos = i
                r.append( (wordpos, spacepos) )
                wordpos, spacepos = i, i
                innerspace = False
                continue
                
            else : # for chnchr
                wordpos, spacepos = i+1, i+1
                #r.append( (wordpos, spacepos) )
                innerspace = False
                onword = False
                continue
                
        else :
            
            if c in letter :
                r.append( (wordpos, spacepos) )
                wordpos, spacepos = i, i
                onword = True
                innerspace = False
                continue
                
            elif c in initials :
                r.append( (wordpos, spacepos) )
                wordpos, spacepos = i, i
                onword = True
                innerspace = True
                continue
                
            elif c in tails :
                onword = True
                spacepos = wordpos
                innerspace = False
                continue
                
            elif c in '\t\r\n' :
                spacepos = i
                r.append( (wordpos, spacepos) )
                wordpos, spacepos = i, i
                innerspace = False
                continue
                
            else : # for chnchr
                wordpos, spacepos = i+1, i+1
                r.append( (wordpos, spacepos) )
                innerspace = False
                onword = False
                continue
                
    r.append( (wordpos, spacepos) )
    
    return r
    
    