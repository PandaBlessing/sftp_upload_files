#!/usr/bin/python
# coding:utf-8


import os
import paramiko
import loadConfig
import files_delete


class MyParamiko(object):
    def __init__(self):
        '''
        封装paramiko的操作服务器类
        '''
        config = loadConfig.load_json()
        setting = self.setting = config[config['start']]
        # print('setting=== ', setting)

        self.host = setting['host']
        self.pwd = setting['pwd']
        self.port = setting['port']
        self.user = setting['user']
        # self.private_key = paramiko.RSAKey.from_private_key_file(
        # '/Users/panda/.ssh/id_rsa')

        # 下载文件或者文件夹到指定位置
        self.download_file = setting['download_file']
        self.storage_path = setting['storage_path']
        # 上传文件或者文件夹到指定位置
        self.upload_path = setting['upload_path']
        self.upload_file = setting['upload_file']
        # 删除文件或者文件夹
        self.delete_file = setting['delete_file']
        self.not_upload_list = setting['not_upload_list']

        self._connect_remote_server()

    def _connect_remote_server(self):
        '''
        建立服务器链接
        :return:
        '''
        print('---Start to remote server---\n')
        # 链接远程服务器
        sf = self.sf = paramiko.Transport((self.host, self.port))
        # sf.connect(username=self.user, pkey=self.private_key)
        sf.connect(username=self.user, password=self.pwd)

        return sf

    def connect_sftp(self):
        '''
        建立sftp链接
        :return:
        '''
        print('Start to SFTP:')
        sftp = paramiko.SFTPClient.from_transport(self.sf)

        return sftp

    def close(self):
        '''
        关闭服务器端链接
        :return:
        '''
        self.sf.close()
        print('\n---End to remote server.---')

    def connect_ssh(self):
        '''
        建立ssh链接
        :return:
        '''
        print('Start to SSH:')
        # 创建SSH对象
        ssh = paramiko.SSHClient()
        ssh._transport = self.sf
        # 允许链接不在know_hosts文件中的主机
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        console = ssh.invoke_shell()
        console.keep_this = ssh

        return ssh

    def cmd(self, ssh, command):
        '''
        建立ssh链接后，执行服务器指令
        :param ssh:
        :param command:
        :return:
        '''
        stdin, stdout, stderr = ssh.exec_command(command)
        result = stdout.read()
        str_result = str(result, encoding='utf-8')
        print(str_result)
        result_err = stderr.read()
        if result_err is None:
            print(str(result_err, encoding='utf-8'))

    def get(self, sftp, remote_file, local_file):
        '''
        下载单个文件
        :param sftp:
        :param remote_file:
        :param local_file:
        :return:
        '''
        print('开始下载文件=== ', remote_file)
        sftp.get(remote_file, local_file)
        print('下载完成,保存在=== ', local_file)

    def put(self, sftp, local_file, remote_file):
        '''
        上传单个文件
        :param sftp:
        :param local_file:
        :param remote_file:
        :return:
        '''
        not_upload_list = self.not_upload_list
        base_name = os.path.basename(local_file)
        if base_name in not_upload_list:
            print('该文件不上传=== ', base_name)
            return

        print('开始上传文件=== ', local_file)
        sftp.put(local_file, remote_file)
        print('上传完成,保存在=== ', remote_file)

    def get_dir(self,sftp,remote_dir,local_dir):
        # all_files = self.__get_all_files_in_remote_dir(sftp,remote_dir)
        # print(all_files)
        # for x in all_files:
        #     file_path =
        pass

    def put_dir(self,sftp,local_dir, remote_dir):
        try:
            sftp.mkdir(remote_dir)
        except Exception as e:
            print(e)

        # 去掉路径字符串最后的字符'/'，如果有的话
        if local_dir[-1] == '/':
            local_dir = local_dir[0:-1]

        for root,dirs,files in os.walk(local_dir):
            for filespath in files:
                local_file = os.path.join(root,filespath)
                a = local_file.replace(local_dir + '/','')
                remote_file = os.path.join(remote_dir,a)
                try:
                    self.put(sftp,local_file,remote_file)
                except Exception as e:
                    sftp.mkdir(os.path.split(remote_file)[0])
                    print('创建目录=== ', os.path.split(remote_file)[0])
                    self.put(sftp,local_file,remote_file)
            for name in dirs:
                local_path = os.path.join(root, name)
                a = local_path.replace(local_dir + '/','')
                remote_path = os.path.join(remote_dir,a)
                try:
                    sftp.mkdir(remote_path)
                    print('创建目录=== ', remote_path)
                except Exception as e:
                    print(e)
        print('上传完成！')

    def upload_py_server(self,sftp,callback=None):
        '''
        上传删除服务端文件的py文件
        '''
        file_delete_name = 'files_delete.py'
        parent_dir = os.path.dirname(self.upload_path)
        print('上传=== ', parent_dir)
        sftp.put(file_delete_name, os.path.join(
            parent_dir, file_delete_name))
        print('上传py文件完成！')


if __name__ == "__main__":
    # 删除本地目录
    config = loadConfig.load_json()
    setting = config[config['start']]
    # files_delete.delete(setting['storage_path'])

    # 链接远程服务器
    my_connect = MyParamiko()
    # 链接ssh
    ssh = my_connect.connect_ssh()
    # 执行指令
    # my_connect.cmd(ssh, 'cd /var/www/pb_me \n ls \n python files_delete.py')

    # 链接sftp
    sftp = my_connect.connect_sftp()

    # 下载文件
    # 服务器文件属性
    # base_name = os.path.basename(my_connect.download_file)
    # my_connect.get(sftp, my_connect.download_file,
    #                os.path.join(my_connect.storage_path, base_name))

    # 上传删除服务端文件的py文件,配置为true时，上传，否则不上传
    if config['is_need_upload_py']:
        my_connect.upload_py_server(sftp)

    # 执行删除指令
    my_connect.cmd(ssh, 'cd %s \n python files_delete.py' % (os.path.split(my_connect.upload_path)[0]))
    # my_connect.cmd(ssh, 'cd ' + os.path.split(my_connect.upload_path)[0] + '\npython files_delete.py')
    # 上传目录
    my_connect.put_dir(sftp, my_connect.upload_file, my_connect.upload_path)
    # 关闭远程服务器链接
    my_connect.close()
