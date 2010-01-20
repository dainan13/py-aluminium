

class Printer():
    
    def __init__ ():
        
        return
    
    @staticmethod
    def dparser( d ):
        '''
        'A' => [{None:'A'}]
        ['A'] => [{None:'A'}]
        ['A',{'B':'C'}] => [{None:'A'},{'B':'C'}]
        {} => []
        {'A':'B'} => [{'A':'B'},]
        {'A':'B','C':'D'} => [{'A':'B','C':'D'},]
        [{'A':'B','C':'D'},] => [{'A':'B','C':'D'},]
        {'A':{'B':'C','D':'E'}} => [{None:'A','B':'C','D':'E'},]
        {'A':['B','C']} => [{'A':['B','C']}]
        '''
        
        return