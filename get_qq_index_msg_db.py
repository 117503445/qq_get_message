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
                lst[0] = lst[0].replace('ZzZ0', '').replace('ZzZ1', '')

                line = '|'.join(lst)
                if _filter(line):
                    f.write(line+'\n')
            except:
                pass
