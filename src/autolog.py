
import easydecorator

class MyException(Exception):

    def my_hook(self):
        print('---> my_hook() was called');

    def __init__(self, *args, **kwargs):
        global BackupException;
        self.my_hook();
        return BackupException.__init__(self, *args, **kwargs);


BackupException = Exception
Exception = MyException







if __name__ == '__main__':
    pass