# -*- coding:UTF-8 -*-
import sys
import re
import os

ifs = '\\'
dirs = {}
sum = 0

def getfiles(system, arch):
    searchpath = system + ifs + arch
    if searchpath not in list(dirs.keys()):
        dirs[searchpath] = ""
        for file in os.listdir(searchpath):
            dirs[searchpath] = dirs[searchpath] + file
    return dirs[searchpath]

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1:
        args.pop(0)
        for searchfile in args:
            print("[Search]: " + searchfile)
            matchType = re.match(r'.*\.(.*)', searchfile)
            if matchType != None and os.path.isfile(searchfile):
                if matchType.group(1) == 'csv':
                    with open(searchfile, 'r') as csv:
                        for line in csv:
                            params = line.split(',')
                            files = getfiles(params[1], params[2].strip())
                            matchObj = re.search(params[0], files)
                            if matchObj == None:
                                sum = sum + 1
                                print(params[0] + " doesn't exist")
                                
                            #print('name: ' + params[0])
                            #print('system: ' + params[1])
                            #print('arch: ' + params[2].strip())
            print("[End]: " + str(sum) + ' rpms need to be downloaded\n----------------------------')

    print('[Complete]')

