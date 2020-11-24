import re
import pymysql
import string
import requests
from basefunc import compressinst,concateinfer,refreshindex,readcrossinfer,removeblock


conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')

def genecrossinfer(article_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select conf,year,number,authors,inst_info from {} '.format(article_table)
    for i in range(2000,2021):
        where_sql="where year={}".format(i)
        print(where_sql)
        cursor1.execute(sel_sql+where_sql)
        for el in cursor1.fetchall():
            if el[4]==None or el[3]==None or el[4]=='' or el[3]=='':
                continue
            all_inst=re.split(r'[;]',el[4])
            all_author=re.split(r'[;]',el[3])
            if len(all_inst)!=len(all_author):
                print('error in {} {} {}'.format(el[0],el[1],el[2]))
                continue
            cross_infer,inst_info=compressinst(all_inst)
            cross_infer_str=concateinfer(cross_infer)
            inst_info=';'.join(inst_info)
            insert_sql='update {} SET cross_infer="{}",inst_info="{}" where conf="{}" and year={} and number="{}"'.format(article_table,cross_infer_str,inst_info,el[0],el[1],el[2])
            cursor2.execute(insert_sql)
        conn.commit()
    cursor2.close()
    return
def genecrossinfer_usenix(article_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select conf,year,number,authors,inst_info from {} '.format(article_table)
    for i in range(1980,2005):
        where_sql="where year={}".format(i)
        cursor1.execute(sel_sql+where_sql)
        for el in cursor1.fetchall():
            all_inst=re.split(r'[;]',el[4])
            all_author=re.split(r'[;]',el[3])
            if len(all_inst)==1:
                cross_infer=[0 for x in range(len(all_author))]
                cross_infer_str=';'.join(list(map(str,cross_infer)))
            elif len(all_inst)==len(all_author) and el[3]!='' and '"' not in el[4]:
                cross_infer,all_inst=compressinst(all_inst)
                cross_infer_str=concateinfer(cross_infer)
            else:
                print('error in {} {} {}'.format(el[0],el[1],el[2]))
                continue

            
            inst_info=';'.join(all_inst)
            insert_sql='update {} SET cross_infer="{}",all_inst_info="{}" where conf="{}" and year={} and number="{}"'.format(article_table,cross_infer_str,inst_info,el[0],el[1],el[2])
            cursor2.execute(insert_sql)
        conn.commit()
    cursor2.close()
    return
def correctfenblock(article_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql="select year,number,authors,cross_infer,inst_info from {} where authors like '%; %'  or inst_info like '%; %'".format(article_table)
    cursor1.execute(sel_sql)
    for el in cursor1.fetchall():
        all_a=el[2]
        if '; ' in all_a:
            print('author_change')
            print(all_a)
            all_a=re.split(r';',all_a)
            all_a=removeblock(all_a)
            all_a=';'.join(all_a)
        inst_info=el[4]
        cross_infer_str=el[3]
        if '; ' in inst_info:
            print('inst_change')
            cross_infer=readcrossinfer(cross_infer_str)
            ii,inst_info=compressinst(inst_info)
            cross_infer=refreshindex(cross_infer,ii)
            cross_infer_str=concateinfer(cross_infer)
            inst_info=';'.join(inst_info)
        update_sql="update {} set authors='{}',cross_infer='{}',inst_info='{}' where year={} and number={}".format(article_table,all_a,cross_infer_str,inst_info,el[0],el[1])
        cursor2.execute(update_sql)
        conn.commit()
    return 
def correctauthor(author_table,inst_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    cursor3=conn.cursor()
    select_sql='select name,article_tag,inst,country from {} where country=""'.format(author_table)
    cursor1.execute(select_sql)
    for each_line in cursor1.fetchall():
        
        find_sql='select country from {} where inst="{}"'.format(inst_table,each_line[2])
        cursor2.execute(find_sql)
        find_out=cursor2.fetchone()
        if find_out==None:
            print(find_sql)
            continue
        find_co=find_out[0]
        if ';' not in find_co and find_co!='':
            this_co=find_co
        else:
            continue
        print(each_line[1:3])
        modify_sql='update {} set country="{}" where name="{}" and article_tag="{}"'.format(author_table,this_co,each_line[0],each_line[1])
        cursor3.execute(modify_sql)
        conn.commit()
    return


if __name__=='__main__':
    #correctauthor('all_author_ccs','ori_inst')
    #genecrossinfer_usenix('all_article_usenix')
    #genecrossinfer('article_info_usenix')
    #print(readcrossinfer('0:1;0:1;0:1;0:1;0;1'))
    #print(refreshindex([[1,2,3],[2,4]],[[0,1],[1,2],[3,1],[2,3],[1,3]]))
    correctfenblock('article_info_usenix')
