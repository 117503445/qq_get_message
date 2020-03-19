# qq_get_message

2020年从安卓QQ数据库提取聊天记录

## 前言

此博客写于 2020.3.19 ，QQ版本 8.3.0

相关 Github 项目文件见 <https://github.com/117503445/qq_get_message>

## 如何获得数据库文件

首先需要已经取得 ROOT 权限的 Android 手机，使用RE管理器或其他方式提取

- /data/data/com.tencent.mobileqq/databases/QQ号.db
- /data/data/com.tencent.mobileqq/databases/slowtable_QQ号.db
- /data/data/com.tencent.mobileqq/databases/QQ号-IndexQQMsg.db
- /data/data/com.tencent.mobileqq/files/imei

其中3个db文件都是Sqlite3数据库，在 Windows 上可以使用 Database.NET 等软件打开。

接下来介绍如何获取聊天记录。

## QQ号-IndexQQMsg.db

参考了 <https://gist.github.com/recolic/02ba2e2dbae20f216c73b84baa91a39e> 并修改脚本，简化操作。

这个数据库储存了最近21天的数据。

这个数据库没有进行加密，只进行了可逆的 Base64 编码，所以可以进行便捷的还原。

我们需要的 数据Table 是 IndexContent_content

将 Python3 脚本放在和 QQ号-IndexQQMsg.db 相同的路径

修改 index_db_path 变量并运行

```python3
import sys
import base64
import datetime
import sqlite3

#输入一行,返回bool,决定是否保留这一行
def _filter(line):
    # return '111222333' in line
    # return '257112220' in line
    return True


def decode_qtimestamp(s):
    #    print('debug', s, file=sys.stderr)
    if s == '':
        return 0
    ts = base64.b64decode(s)[4:8]
    return sum([int(ts[i])*(256**(3-i)) for i in range(4)])


def timestamp_to_str(int_ts):
    return datetime.datetime.fromtimestamp(int_ts).strftime('%Y-%m-%d %H:%M:%S')

#IndexQQMsg.db的路径,请修改
index_db_path = '{QQ_Number}-IndexQQMsg.db'

if __name__ == "__main__":
    conn = sqlite3.connect(index_db_path)
    c = conn.cursor()
    lines = c.execute('select * from IndexContent_content;')

    with open(f'{index_db_path}.txt', 'w', encoding='utf8') as f:
        for line in lines:
            try:
                timestamp = timestamp_to_str(decode_qtimestamp(line[-1]))
                lst = [timestamp]

                line = line[:-1]

                for i in [5, 6, 2]:
                    lst.append(base64.b64decode(
                        line[i]).decode(errors='ignore'))
                lst[1] = lst[1].replace('ZzZ0', '').replace('ZzZ1', '')

                line = '|'.join(lst)
                if _filter(line):
                    f.write(line+'\n')
            except:
                pass

```

## QQ号.db

参考了 <https://github.com/roadwide/qqmessageorutput> 并修改脚本，简化操作

这个数据库储存了最近21天的数据。

但是进行了异或加密。对于老版本的QQ，加密的Key就是手机的IMEI号，可以在 /data/data/com.tencent.mobileqq/files/imei 中查看。但是新版本中似乎更改了加密的key，可以参考 <https://github.com/Yiyiyimu/QQ_History_Backup> 中的解决方案。

每个好友占一个 Table，名字是 mr_friend_QQ号的MD5的16进制的字母大写

每个群占一个 Table，名字是 mr_troop_QQ群号的MD5的16进制的字母大写

将 Python3 脚本放在和 QQ号.db 相同的路径

修改 dbfile 和 key 变量并运行

```python3
from _overlapped import NULL
import hashlib
import sqlite3
import time
import os


class QQoutput():
    def __init__(self, db, key):
        self.key = key  # 解密用的密钥
        self.c = sqlite3.connect(db).cursor()

    # msgdata mode=0
    # other mode=1
    def fix(self, data, mode):
        if(mode == 0):
            rowbyte = []
            for i in range(0, len(data)):
                rowbyte.append(data[i] ^ ord(self.key[i % len(self.key)]))
            rowbyte = bytes(rowbyte)
            try:
                msg = rowbyte.decode(encoding='utf-8')
            except:
                msg = NULL
            return msg
        elif(mode == 1):
            str = ''
            try:
                for i in range(0, len(data)):
                    str += chr(ord(data[i]) ^ ord(self.key[i % len(self.key)]))
            except:
                str = NULL
            return str

    def message(self, table_name):
        execute = f'select msgData,senderuin,time from {table_name}'
        cursor = self.c.execute(execute)
        allmsg = []
        for row in cursor:
            msgdata = row[0]
            uin = row[1]
            ltime = time.localtime(row[2])

            sendtime = time.strftime("%Y-%m-%d %H:%M:%S", ltime)
            msg = self.fix(msgdata, 0)
            senderuin = self.fix(uin, 1)

            amsg = []
            amsg.append(sendtime)
            amsg.append(senderuin)
            amsg.append(msg)
            allmsg.append(amsg)
        return allmsg

    def output(self, dbfile):
        execute = f"SELECT name FROM sqlite_master WHERE type ='table' AND (name LIKE 'mr_friend_%' OR name LIKE 'mr_troop_%') ;"
        rows = self.c.execute(execute)
        lst_table_name = []
        for row in rows:
            # row[0] like mr_friend_{QQ号的MD5的16进制的字母大写}_New
            lst_table_name.append(row[0])

        dir_name = f'{dbfile}.dir'

        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

        for table_name in lst_table_name:

            file = dir_name+'\\' + table_name+".html"
            f2 = open(file, 'w', encoding="utf-8")
            f2.write(
                "<head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\" /></head>")
            allmsg = self.message(table_name)
            for msg in allmsg:
                if msg[2] != 0:
                    try:
                        f2.write("<font color=\"blue\">")
                        f2.write(msg[0])
                        f2.write("</font>-----<font color=\"green\">")
                        f2.write(msg[1])
                        f2.write("</font></br>")
                        f2.write(msg[2])
                        f2.write("</br></br>")
                    except:
                        pass


if __name__ == "__main__":
    # config
    # 储存QQ聊天信息的db文件，qq号.db 或者是 slowtable_qq号.db,记得把文件和py代码放在同目录
    dbfile = ''
    # 解密的key,一般为IMEI,在files/IMEI文件
    key = ''

    q = QQoutput(dbfile, key)
    q.output(dbfile)

```

## slowtable_QQ号.db

slowtable_QQ号.db 储存了21天前的

slowtable_QQ号.db 和 QQ号.db 的数据结构是基本一致的，所以可以直接使用上面的脚本

## 总结

感谢下列参考链接做出的工作

<https://github.com/roadwide/qqmessageoutput>

<https://gist.github.com/recolic/02ba2e2dbae20f216c73b84baa91a39e>

<https://github.com/Yiyiyimu/QQ_History_Backup>

另外，目前因为key的改变，没有实现后面2个数据库的记录提取，但是 <https://github.com/Yiyiyimu/QQ_History_Backup> 中可以使用近期聊天记录进行提取，而近期聊天记录可以通过第一个数据库提取，这样就可以获得21天前的记录。不过目前我还没有实践 <https://github.com/Yiyiyimu/QQ_History_Backup> 中的方法，所以只是作为思路参考。

如果帮助到了你，请给个 star ：D <https://github.com/117503445/qq_get_message>
