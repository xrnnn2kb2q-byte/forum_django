# md5

import hashlib

def calc_md5(password):
    md5_obj = hashlib.md5()
    md5_obj.update(password.encode('utf-8'))
    return md5_obj.hexdigest()

def get_default_pwd():
    md5_obj = hashlib.md5()
    md5_obj.update('123456'.encode('utf-8'))
    return md5_obj.hexdigest()