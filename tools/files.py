import os
from myexceptions import ConfigFileEmpty


def check_config_file(path):
    while not os.getcwd().endswith('mySC'):
        os.chdir('..')
    path = os.path.join(os.getcwd(), path)
    if os.path.exists(path):
        if not os.path.getsize(path):
            raise ConfigFileEmpty()
        return True
    else:
        os.mkdir(path.split('/')[0])
        open(path, 'x')
        raise ConfigFileEmpty()
