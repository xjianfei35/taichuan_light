import os
#1.delete current dir __pycache__

def del_dir(pdir):
    for root, subroot, files in os.walk(pdir):
        #删除文件
        print("root",root)
        print("subroot",subroot)
        for file in files:
            file_path=root+"/"+file;
            print("del",file_path)
            os.remove(file_path)

        #删除子目录
        for subdir in subroot:
            subdir_path = root+"/"+subdir
            #del_dir(subdir_path)
            print("del dir",subdir_path)
            os.rmdir(subdir_path)
        print("del root",root)
        os.rmdir(root)

def del_sub_dir(pdir,dir_name):
    for root, subroot, files in os.walk(pdir):
        for subdir in subroot:
            if(subdir==dir_name):
                subdir_path=root+"/"+subdir
                print("del dir",subdir_path)
                del_dir(subdir_path)

del_sub_dir("./test","tmp")                        
#del_dir("./test/tmp")
