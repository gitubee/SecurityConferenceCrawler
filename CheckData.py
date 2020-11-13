import re
import pymysql

conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')

def checkarticlepage(article_table,page_str):
    global conn
    cursor1=conn.cursor()
    now_end=2
    sel_sql='select conf,year,{},{} from {}'.format(page_str[0],page_str[1],article_table)
    for i in range(2010,2021):
        where_sql=' where year={}'.format(str(i))
        cursor1.execute(sel_sql+where_sql)
        now_end=1
        for el in cursor1.fetchall():
            tag=str(el[0])+';'+str(el[1])+';'+str(el[2])
            if el[2]=='' or el[3]=='':
                print(tag+'error1')
                continue
            s_p=int(el[2])
            e_p=int(el[3])
            if s_p==e_p or now_end<s_p:
                print(tag+'error2')
                now_end=e_p+2
            now_end=e_p+2
    return
if __name__=='__main__':
    checkarticlepage('article_info_springer',['start_page','end_page'])
