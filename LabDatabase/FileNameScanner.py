# import os
from os import path
# import re
from re import split,compile,search

import ControllerModule



#添加分析括号里面的信息的功能
#(\(?)(.*)(\)?)
class FileNameScanner:
    # TODO:  TEMP
    # FileNameRE = compile(r'(((^[a-zA-Z]+)(\d+))(-|_||))(((\d+)((-|_||)))+)(\.)(\S+)')
    # FileNameRE = compile(r'^([a-zA-Z0-9]+)(-|_([a-zA-Z0-9]+))*.*')
    FileNameRE = compile(r'([a-zA-Z0-9_\|-]+)\.(\w+)')
    # PartFileNameRE = compile(r'[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+\.*')
    # BackboneFileNameRE = compile(r'[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+\.*')
    # PlasmidFileNameRE = compile(r'[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+_|-|\|[a-zA-Z0-9]+(_|-|\|[a-zA-Z0-9]+)+\.*')

    #Temp Regular Equal
    # FileNameRE = compile(r'(^[A-Za-z0-9]+)((-|_)((\(?.*\)?)*)(\..*)$)?')
    #因为读出来的地址是整个文件的路径, 所以需要对整个文件名进行分割, 取出来最后的一段文件名字部分

    def __init__(self, loc, fname = None):
        if fname is None:
            self.path = loc
            self.loc, self.fname = path.split(self.path)
        else:
            self.loc = loc
            self.fname = fname
            self.path = path.join(loc, fname)


    def NameForm(self):
        FileSpilt = []
        # m = FileNameScanner.FileNameRE.match(self.fname)
        res = FileNameScanner.FileNameRE.search(self.fname)
        if(res!=None):
            ControllerModule.setIsSuitRE(True)
            ComponentList = split(r'[-_\|\.]',self.fname)
            for i in range(0,len(ComponentList)-1):
                FileSpilt.append(ComponentList[i])
        else:
            ControllerModule.setIsSuitRE(False)
        return FileSpilt
    

if __name__ =='__main__':
    fs = FileNameScanner(r'c:\Users\admin\Desktop\DSF011-level3-pnpA-pnpB-pnpCDEFG-p15A-specR-EH.dna')
    print(fs.NameForm())