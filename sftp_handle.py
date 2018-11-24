#!/usr/bin/python
# coding:utf-8


import os
import paramiko
import loadConfig


class MyParamiko(object):
    def __init__(self):
        '''
        封装paramiko的操作服务器类
        '''
        config = loadConfig.load_json()
        setting = self.setting = config[config['start']]

        self.host = setting['host']
        self.pwd = setting['pwd']
        self.port = setting['port']
        self.user = setting['user']
        # self.private_key = paramiko.RSAKey.from_private_key_file(
        # '/Users/panda/.ssh/id_rsa')

        # 上传文件或者文件夹到指定位置
        self.remote_path = setting['remote_path']
        self.local_path = setting['local_path']
        # 不需要上传的文件列表
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

        print('上传文件=== ', base_name)
        sftp.put(local_file, remote_file)
        print('上传完成,储存位置=== ', os.path.dirname(remote_file))

    def put_dir(self, sftp, local_dir, remote_dir):
        '''
        上传目录
        '''
        try:
            sftp.mkdir(remote_dir)
        except Exception as e:
            print(e)

        # 去掉路径字符串最后的分隔符'/'，如果有的话
        str_sep = os.sep
        if local_dir[-1] == str_sep:
            local_dir = local_dir[0:-1]

        for root, dirs, files in os.walk(local_dir):
            for filespath in files:
                local_file = os.path.join(root, filespath)
                a = local_file.replace(local_dir + str_sep, '')
                remote_file = os.path.join(remote_dir, a)
                try:
                    self.put(sftp, local_file, remote_file)
                except Exception as e:
                    print(e)

            for name in dirs:
                local_path = os.path.join(root, name)
                a = local_path.replace(local_dir + str_sep, '')
                remote_path = os.path.join(remote_dir, a)
                try:
                    sftp.mkdir(remote_path)
                    print('创建目录=== ', remote_path)
                except Exception as e:
                    print(e)
        print('上传完成！')

    def delete_sftp_files(self, sftp, path):
        '''
        删除远程服务器文件
        '''
        print('开始删除该处文件==== ', path)

        def delete(p):
            try:
                files = sftp.listdir(p)
                if files is None or len(files) == 0:
                    try:
                        sftp.rmdir(p)
                        print('删除目录=== ', p)
                    except Exception as e:
                        print('不存在该目录=== ', e)
                        pass
                else:
                    for file in files:
                        try:
                            # 尝试删除文件
                            sftp.remove(os.path.join(p, file))
                            print('删除文件=== ', file)
                        except Exception as e:
                            try:
                                # 尝试删除目录
                                sftp.rmdir(os.path.join(p, file))
                                print('删除目录=== ', os.path.join(p, file))
                            except Exception as e:
                                # 目录不为空时，递归删除子目录
                                delete(os.path.join(p, file))
                    # 尝试删除该目录所在的目录
                    delete(p)
            except Exception as e:
                print('不存在该目录=== ', e)
                pass
        delete(path)


if __name__ == "__main__":
    # 链接远程服务器
    my_connect = MyParamiko()
    # 链接ssh
    # ssh = my_connect.connect_ssh()
    # 执行指令
    # my_connect.cmd(ssh, 'cd /var/www/pb_me \n ls \n python files_delete.py')

    # 链接sftp
    sftp = my_connect.connect_sftp()

    # 删除远程服务器上的目录
    my_connect.delete_sftp_files(sftp, my_connect.remote_path)
    # 上传目录
    my_connect.put_dir(sftp, my_connect.local_path, my_connect.remote_path)
    # 关闭远程服务器链接
    my_connect.close()
