import requests
import time
import re
import sys
from bs4 import BeautifulSoup

rpms = []
archs = ['aarch64', 'x86_64']
systems = ['Fedora', 'CentOS', 'Mageia']
searchurl = 'http://rpmfind.net/linux/rpm2html/search.php?'
downloadurl = 'http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/'
VALID_LENGTH = 2000 # 用于判断downloadurl是否有效

'''
[get url]: /linux/RPM/fedora/devel/rawhide/aarch64/g/gcc-9.2.1-1.fc32.aarch64.html
[download url]: http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/g/gcc-9.2.1-1.fc32.aarch64.rpm
                http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/g/gcc-4.8.5-36.el7.x86_64.rpm

[get url]: /linux/RPM/fedora/devel/rawhide/aarch64/b/bash-5.0.7-3.fc31.aarch64.html
[download url]: http://rpmfind.net/linux/fedora/linux/development/rawhide/Everything/aarch64/os/Packages/b/bash-5.0.7-3.fc31.aarch64.rpm
'''

# 下载链接的请求参数
class Requestparams:
    def __init__(self, name, system, arch):
        self.name = name
        self.system = system
        self.arch = arch

# 通过解析html获取rpm的下载链接
def getdownloadurl(name, system, arch):
    # tmpurl = url + getfirstletter(name) + '/' + name + getversion(name) + '.' + arch + '.rpm'
    surl = searchurl + 'query=' + name + '&submit=Search+...&system=' + system + '&arch=' + arch
    html = requests.get(surl)
    if html.status_code == 200:
        soup = BeautifulSoup(html.text, 'html.parser')
        tbody = soup.find_all('tbody')[1]
        children = list(tbody.find_all('a'))
        link = children[0]['href']
        print('[Get url]:\n%s' % link)
        matchObj = re.search(r'.*(/.*).html', link)
        durl = downloadurl + name[0] + matchObj.group(1) + '.rpm'
        print('[Download url]:\n%s' % durl)
        return durl
    else:
        print('[Failed to get download url]')
        return None
    

# 通过getdownloadurl函数获得的url下载rpm
def downloadrpm(rpmname, durl):
    r = requests.get(durl, stream=True)
    print(r.headers)

    if int(r.headers['Content-Length']) > VALID_LENGTH:
        print('[Downloading]:\n%s' % durl)
        with open(rpmname, 'wb') as f:
            f.write(r.content)
    else:
        print('[Wrong url]:\n%s' % durl)

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
        print('[Wrong param]: %s' % arch)
        return None
    
    return Requestparams(name, system, arch)

# 通过文本方式批量下载rpm
def downloadbyfile():
    matchObj = re.match(r'.*\.(.*)', sys.argv[1])
    typeoffile = matchObj.group(1)
    print(typeoffile)
    if typeoffile == 'csv':
        ifs = ','
    else:
        ifs = ' '
    with open(sys.argv[1], "r") as f:
        for line in f:
            fparams = line.strip().split(ifs)
            print(fparams)
            tmpdownloadurl = getdownloadurl(fparams[0], fparams[1], fparams[2])
            if tmpdownloadurl == None:
                continue
            matchObj = re.search(r'.*/(.*.rpm)', tmpdownloadurl)
            rpmname = matchObj.group(1)
            downloadrpm(rpmname, tmpdownloadurl)

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
                    downloadrpm(rpmname, tmpdownloadurl)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        downloadbyfile()
    else:
        downloadbycli()

    print('[Complete]')