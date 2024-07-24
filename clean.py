import os
#1.delete current dir __pycache__
dir  = "./__pacache__"

def del_sub_dir(pdir):
    for root, subroot, files in os.walk(dir):
        for file_name in files:
            print(file_name)

del_sub_dir(dir)                        
