=========================
 Easychecker
=========================




 Designs
=========================

A simple way to parse the docstring to datastructures.

In common, we often write a simple annotation as docstring in functin or method.
it explain some constants we used, or other some useful information. but when
we change the constant or other, we often forget to update the docstring.
If the constant is defined in docstring, not in code, the behavior and act will
be same at all.

the parser must supported common document format ::

    d = '''
        a test docstring
        
        ##!# Metas1                                                      .object
        name : foo
        classification : test
        version : 1.1
        
        ##!# Metas2                                                       .value
        array(
            #.D : hex(32),
            #.E : ascii(-32),
        )
        
        ##!# Arguments1                                                   .table
        !Name          !Format                      !Required  !Default
        A              ascii(<255)                  No
        B              object(alnum(20):array(acl)) No         {}
        P              object(                      Yes
        !                 #.number:string
        !              )
        
        ##!# Arguments2                                                   .table
        H        34677         No    D
        I           34         No
        J          234         Yes
        '''

and you will get ::

    >>> parsedocstring(d)
    {'Metas1':{'name':'foo','classification':'test','version':'1.1'},
     'Metas2':'array(\n    #.D : hex(32),\n    #.E : ascii(-32),\n)',
     'Arguments1':[{'Name':'A','Format':'ascii(<255)','Required':'No','Default':''},
                   {'Name':'B','Format':'object(alnum(20):array(acl))','Required':'No','Default':'{}'},
                   {'Name':'P','Format':'object(\n   #.number:string\n)','Required':'Yes','Default':''},
                  ],
     'Arguments2':[['H','34677','No','D'],['I','34','No',''],['J','234','Yes','']],
    }