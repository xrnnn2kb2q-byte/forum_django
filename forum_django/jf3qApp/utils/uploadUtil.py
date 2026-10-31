import os
import random

def get_default_img():
    return '/static/upload/noimg.jpg'

def upload(file, package):
    format = file.name[file.name.rfind('.'):len(file.name)]
    print(format)
    abpath = os.path.abspath(os.path.dirname(__file__)).replace('utils','') + 'static/upload/' + package + '/'
    print(abpath)
    if not os.path.exists(abpath):
        os.makedirs(abpath)

    fname = ''
    for i in range(1,20):
        fname += str(random.randint(1,10))
    abpathfname = abpath + fname + format
    f = open(abpathfname,'wb')
    for chunk in file.chunks():
        f.write(chunk)
    f.close()
    return '/static/upload/' + package + '/' + fname + format

def delfile(path):
    abpath = os.path.abspath(os.path.dirname(__file__)).replace('utils','')
    f = abpath + path
    d = get_default_img()
    if d in f:
        print('------default img not del------')
        return
    if os.path.exists(f):
        print('------delete old img------')
        print(f)
        os.remove(f)

if __name__ == '__main__':
    delfile('/upload/faceimg/noimg.jpg')