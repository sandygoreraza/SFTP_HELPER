import datetime
import os
import shutil
import logging
import pysftp
import configparser

class SFTPHelper:

    def __init__(self, shost, susername, spassword, sport):
        self.shost = shost
        self.susername = susername
        self.spassword = spassword
        self.sport = sport

        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None
        # self.cnopts.hostkeys.load('known_hosts')
        self.sftp = pysftp.Connection(host=shost, username=susername, password=spassword, port=sport
                                      ,cnopts=self.cnopts
                                      )

    def createdatefolders(self, basepath):
        today = datetime.datetime.now()
        year = today.strftime("%Y")
        weekday = today.strftime("%A")
        monthname = today.strftime("%B")
        month = today.strftime("%m")
        day = today.strftime("%d")
        mydir = os.path.join(basepath, year, month + "-" + monthname, day + "-" + weekday)

        if not os.path.exists(mydir):
            os.makedirs(mydir)

        return mydir

    def downloadfile(self, pathlocal, pathremote):
        self.sftp.get(localpath=pathlocal, remotepath=pathremote)

    def backupfile(self, src, dst):
        if not os.path.exists(dst):
            os.makedirs(dst)
        shutil.copy(src, dst)

    def uploadfile(self, pathlocal, pathremote):
        self.sftp.put(remotepath=pathremote, localpath=pathlocal)

    def LocalFileExist(self, localpath):
        FileExist = os.path.isfile(localpath)
        if (FileExist):
            return True
        else:
            return False

    def eraselocalfile(self, file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print("Error encountered in deleting file " + repr(e))
            logging.info("Error encountered " + repr(e))

    def deletefile(self, pathremote):
        self.sftp.remove(remotefile=pathremote)

    def putfilesremote(self, pathremote, pathlocal,logging):

        filelist = os.listdir(pathlocal)  # remove the value 'JavaScript' from the list

        if 'Backup' in filelist:  # check if 'Backup' folder exist
            filelist.remove('Backup')  # to prevent permission error as it is a directory no a file for upload

        for filename in filelist:
            self.uploadfile(pathlocal + '/' + filename, pathremote + '/' + filename)

            if self.LocalFileExist(pathlocal + '/' + filename):  # delete file from local server if exist
                self.eraselocalfile(pathlocal + '/' + filename)

            print('file ' + filename + ' has been uploaded  from local path ' + pathlocal)
            logging.info('file ' + filename + ' has been uploaded  from local path ' + pathlocal)

    def closesftp(self):
        self.sftp.close()

    def getfiles(self, pathremote, pathlocal, logging):
        filelist = self.sftp.listdir(pathremote)
        for filename in filelist:
            self.downloadfile(pathlocal + '/' + filename, pathremote + '/' + filename)
            self.backupfile(pathlocal + '/' + filename, pathlocal + '/Backup')
            self.deletefile(pathremote + '/' + filename)
            print('file ' + filename + ' has been downloaded from ' + pathremote + '/' + filename)
            logging.info('file ' + filename + ' has been downloaded from ' + pathremote + '/' + filename)
            logging.info('file ' + filename + ' has been removed from ' + pathremote + '/' + filename)

    def closesftp(self):
        self.sftp.close()


class FTPHelper:
    def __init__(self):
        pass

    def createdatefolders(self, basepath):
        today = datetime.datetime.now()
        year = today.strftime("%Y")
        weekday = today.strftime("%A")
        monthname = today.strftime("%B")
        month = today.strftime("%m")
        day = today.strftime("%d")
        mydir = os.path.join(basepath, year, month + "-" + monthname, day + "-" + weekday)

        if not os.path.exists(mydir):
            os.makedirs(mydir)
        print(mydir)
        return mydir



if __name__ =="__main__":
    k = FTPHelper()
    config = configparser.ConfigParser()
    config.read('settings.config')

    basePath = config['local_path']['base_path']
    from_server = config['from_server']
    to_server = config['to_server']

    logging.basicConfig(filename=os.path.join(k.createdatefolders(basePath + '\\Logs'), 'logs.txt'),
                        level=logging.INFO, filemode='a',
                        format='%(name)s - %(levelname)s - %(asctime)s -        %(message)s')
    for i in range(5):
        try:
            port = config['from_server']['port']
            iport = int(port)

            fromsftp = SFTPHelper(from_server['server'], from_server['username'], from_server['password'],iport)
            logging.info('Connected to SFTP in ' + str(i + 1) + ' attempt- to download file')
            print('Connected to SFTP in ' + str(i + 1) + ' attempt- to download file')
            fromsftp.getfiles(from_server['reception_path'], k.createdatefolders(basePath + '\\reception'),logging)
            fromsftp.getfiles(from_server['delivery_path'], k.createdatefolders(basePath + '\\delivery'),logging)

        except Exception as e:
            if i < 4:
                continue
            else:
                print("Failed to connect to Source server - error: ")
                raise
        break

    print("******now uploading files******")
    logging.info("******now uploading files******")

    for i in range(5):
        try:
            port = config['to_server']['port']
            iport = int(port)

            putfilessftp = SFTPHelper(to_server['server'], to_server['username'], to_server['password'], iport)
            logging.info('Connected to SFTP in ' + str(i + 1) + ' attempt - to upload files')
            print('Connected to SFTP in ' + str(i + 1) + ' attempt - to upload files')
            putfilessftp.putfilesremote(to_server['reception_path'], k.createdatefolders(basePath + '\\reception'),logging)
            putfilessftp.putfilesremote(to_server['delivery_path'], k.createdatefolders(basePath + '\\delivery'),logging)

        except Exception as e:
            if i < 4:
                continue
            else:
                print("Error encountered " + repr(e))
                logging.info("Error encountered " + repr(e))
                raise

        break



