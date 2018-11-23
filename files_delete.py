#!/user/bin/python
# coding:utf-8

import shutil


def delete(path):
    print('delete old files.')
    shutil.rmtree(path)
    # print('delete finish!')


if __name__ == '__main__':
    delete('res')