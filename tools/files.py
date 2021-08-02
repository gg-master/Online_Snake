import os
from myexceptions import ConfigFileEmpty


def check_config_file(path):
    if os.getcwd().endswith("tools"):
        os.chdir('..')
    if os.path.exists(path):
        if not os.path.getsize(path):
            raise ConfigFileEmpty()
        return True
    else:
        os.mkdir(path.split('/')[0])
        open(path, 'x')
        raise ConfigFileEmpty()
