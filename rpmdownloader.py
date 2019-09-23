# -*- coding:UTF-8 -*-
import requests
import time
import re
import sys
import os
import platform
import time
from bs4 import BeautifulSoup

ifdebug = False # debug模式只打印最后下载链接的请求头，不真正下载
archs = ['aarch64', 'x86_64-latest']
systems = ['Fedora', 'OpenSuSE', 'CentOS']
searchurl = 'http://rpmfind.net/linux/rpm2html/search.php?'
downloadurl = 'http://rpmfind.net'
ifs = '/' # 默认为Linux系统path分隔符
VALID_LENGTH = 2000 # 用于判断downloadurl是否有效

'''
[download url]: http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/g/gcc-9.2.1-1.fc32.aarch64.rpm
'''

# 下载链接的请求参数
class Requestparams:
    def __init__(self, name, system, arch):
        self.name = name
        self.system = system
        self.arch = arch

# 通过解析html获取rpm的下载链接
def getdownloadurl(name, system, arch):
    link = None
    # CentOS从CentOS官网获取RPM，其他系统从rpmfind上获取
    if system == 'CentOS':
        link = getcentosurl(name, arch)
    else:
        surl = searchurl + 'query=' + name + '&submit=Search+...&system=' + system + '&arch=' + arch
        html = requests.get(surl)
        if html.status_code == 200:
            soup = BeautifulSoup(html.text, 'html.parser')
            if len(soup.find_all('tbody')) > 1:
                tbody = soup.find_all('tbody')[1]
                children = list(tbody.find_all('a'))
                # print(children)
                for child in children:
                    matchObj = re.search(r'.*(.rpm)', child['href'])
                    if matchObj != None:
                        link = downloadurl + child['href']
                        break
    if link == None:
        addlog('[Failed to get download url]: ' + name + '-' + system + '-' + arch)
        print('[Failed to get download url]')
    print('[Download url]:\n%s' % link)
    return link
    
# CentOS系统的RPM从CentOS官方获取
def getcentosurl(name, arch):
    # https://buildlogs.centos.org/centos/7/os/aarch64/Packages/bash-4.2.46-12.el7.aarch64.rpm
    
    surl = 'http://buildlogs.centos.org/centos/7/os/' + arch + '/Packages/'
    htmlpath = gethtmlpath(surl, arch)
    res = None
    if htmlpath != None:
        with open(htmlpath, 'r') as html:
            soup = BeautifulSoup(html, 'html.parser')
            links = list(soup.find_all('a'))
            for link in links:
                matchObj = re.match(r'' + name + '\-[0-9].*', link['href'])
                if matchObj != None:
                    res = surl + link['href']
    return res

# 通过getdownloadurl函数获得的url下载rpm
def downloadrpm(rpmpath, durl):
    # 如果文件已存在且大小不为0，不重复下载
    if os.path.isfile(rpmpath):
        if os.path.getsize(rpmpath) > 0:
            print('[Exist]:\n%s' % rpmpath)
    else:
        r = requests.get(durl, stream=True)
        if ifdebug == False:
            if int(r.headers['Content-Length']) > VALID_LENGTH:
                print('[Downloading]:\n%s' % durl)
                with open(rpmpath, 'wb') as f:
                    f.write(r.content)
            else:
                addlog('[Wrong url]: ' + durl)
                print('[Wrong url]:\n%s' % durl)
        else:
            print(r.headers)

def printmenu():
    print('*************************')
    print('命令编号：')
    print('1.下载RPM')
    print('2.结束')
    print('*************************')

# 通过命令行获取rpm的名称、系统和架构
def getparams():
    name = input('请输入rpm名称：')
    matchObj = re.match(r'([a-zA-Z0-9\-]+)', name)
    if matchObj == None:
        addlog('[Wrong param]: ' + name)
        print('[Wrong param]: %s' % name)
        return None
    print('-------------------------')
    index = 1
    for val in systems:
        print(str(index) + '.' + val)
        index = index + 1
    system = input('请输入system编号：')
    matchObj = re.match(r'([0-9]+)', system)
    if matchObj == None:
        addlog('[Wrong param]: ' + system)
        print('[Wrong param]: %s' % system)
        return None
    print('-------------------------')
    index = 1
    for val in archs:
        print(str(index) + '.' + val)
        index = index + 1
    arch = input('请输入arch编号：')
    matchObj = re.match(r'([0-9]+)', arch)
    if matchObj == None:
        addlog('[Wrong param]: ' + arch)
        print('[Wrong param]: %s' % arch)
        return None
    
    return Requestparams(name, system, arch)

# 通过文本方式批量下载rpm
def downloadbyfile():
    matchObj = re.match(r'.*\.(.*)', sys.argv[1])
    typeoffile = matchObj.group(1)
    print(typeoffile)
    if typeoffile == 'csv':
        paramifs = ','
    else:
        paramifs = ' '
    with open(sys.argv[1], "r") as f:
        for line in f:
            print('-------------------------')
            fparams = line.strip().split(paramifs)
            print(fparams)
            tmpdownloadurl = getdownloadurl(fparams[0], fparams[1], fparams[2])
            if tmpdownloadurl == None:
                continue
            matchObj = re.search(r'.*/(.*.rpm)', tmpdownloadurl)
            rpmname = matchObj.group(1)
            path = getpath(rpmname, fparams[1], fparams[2])
            downloadrpm(path, tmpdownloadurl)

# 通过命令行下载rpm
def downloadbycli():
    while True:
        printmenu()
        cmdnum = input('请输入命令编号：')
        if cmdnum == '2':
            break
        if cmdnum == '1':
            print('-------------------------')
            rparams = getparams()
            if rparams == None:
                continue
            else:
                tmpdownloadurl = getdownloadurl(rparams.name, systems[int(rparams.system) - 1], archs[int(rparams.arch) - 1])
                if tmpdownloadurl == None:
                    continue
                matchObj = re.search(r'.*/(.*.rpm)', tmpdownloadurl)
                rpmname = matchObj.group(1)
                ifdownload = input('Download %s(y/n): ' % rpmname)
                if ifdownload == 'y':
                    path = getpath(rpmname, systems[int(rparams.system) - 1], archs[int(rparams.arch) - 1])
                    downloadrpm(path, tmpdownloadurl)

# 检查准备下载的RPM有没有相应的目录，如果存在就返回相应路径，如果不存在则创建后返回
def getpath(rpmname, system, arch):
    path = system + ifs + arch
    ifExist = os.path.exists(path)
    if not ifExist:
        os.makedirs(path)

    path = path + ifs + rpmname
    print('[Path]: \n%s' % path)
    return path

# 根据操作系统确定目录分隔符
def getifs():
    currentos = platform.system()
    print(currentos)
    if currentos == 'Windows':
        ifs = '\\'
    else:
        ifs = '/'

# 错误日志文件添加记录
def addlog(str):
    if not os.path.exists('logs'):
        os.makedirs('logs')
    with open('logs' + ifs + time.strftime('%Y%m%d', time.localtime()) + '.log', 'a') as log:
        log.write(time.strftime('%H:%M:%S-', time.localtime()) + str + '\n')

# 检查是否存在当天更新的CentOS官网RPM列表的html，如果不存在则获取html并保存，返回html的路径
def gethtmlpath(surl, arch):
    path = 'CentOS' + ifs + arch
    ifExist = os.path.exists(path)
    if not ifExist:
        os.makedirs(path)

    htmlpath = path + ifs + time.strftime('%Y%m%d', time.localtime()) + '.html'
    ifExist = os.path.isfile(htmlpath)
    if not ifExist:
        print('[获取html]：\n%s' % surl)
        html = requests.get(surl)
        if html.status_code == 200:
            with open(htmlpath, 'wb') as htmldoc:
                htmldoc.write(html.content)
        else:
            return None
    
    print('[html path]：\n%s' % htmlpath)
    return htmlpath

# main函数，根据参数判断模式
if __name__ == "__main__":
    getifs()
    if len(sys.argv) > 1:
        downloadbyfile()
    else:
        downloadbycli()

    print('[Complete]')
