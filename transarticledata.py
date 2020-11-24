
import re
import pymysql
import string
import requests
from lxml import etree
from basefunc import removeblock,delsession
conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
ieee_pre_url_list={'base':'https://ieeexplore.ieee.org/','article':'https://ieeexplore.ieee.org/document/','pdf':'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber='}
doi_pre_url_list={'base':'https://doi.org/'}
acm_pre_url_list={'base':'https://dl.acm.org/','conf':'https://dl.acm.org/doi/proceedings/','article':'https://dl.acm.org/doi/','pdf':'https://dl.acm.org/doi/pdf/'}
ndss_pre_url_list={'base':'https://www.ndss-symposium.org/','pdf':'https://www.ndss-symposium.org'}


def gethtmltext(url):#以agent为浏览器的形式访问网页,返回源码,参数是某个论文网页或者会议综述网页的url
      try:
            kv ={'user-agent':'Mozilla/5.0'}
            r=requests.get(url,headers=kv)
            r.raise_for_status()
            r.encoding=r.apparent_encoding
            return r.text
      except:
            return 'error'

def transieee(ieee_table,insert_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select conf,year,title,doi,authors,session_title,ieee_number,ieee_keywords,start_page,end_page from {} '.format(ieee_table)
    insert_sql='insert into {}() values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(insert_table)
    for i in range(1980,1988):
        where_sql="where year={}".format(i)
        cursor1.execute(sel_sql+where_sql)
        number=-1
        for el in cursor1.fetchall():
            number+=1
            #if (el[-1]-el[-2])<5:
                #continue
            if 'Panel' in el[2] or 'Panel' in el[5]:
                continue
            #print(number)
            el=list(el)
            session=el[5]
            session=delsession(session,4,1)
            ieee_num=el[6]
            article_url=ieee_pre_url_list['article']+ieee_num
            pdf_url=ieee_pre_url_list['pdf']+ieee_num
            #authors=';'.join(removeblock(re.split(r'[;]',el[4])))
            #keywords=';'.join(removeblock(re.split(r'[;]',el[7])))
            keywords=el[7]
            insert_data=el[0:2]+[number]+el[2:5]+[session,keywords,article_url,pdf_url]
            cursor2.execute(insert_sql,insert_data)
        conn.commit()
    cursor1.close()
    cursor2.close()
    return
def transccs(ccs_table,insert_table):
    global conn
    global acm_pre_url_list
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select conf,year,title,doi,authors,kind,session,keywords,start_page,end_page from {} '.format(ccs_table)
    insert_sql='insert into {}() values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(insert_table)
    for i in range(2015,2021):
        where_sql="where year={}".format(i)
        cursor1.execute(sel_sql+where_sql)
        number=-1
        for el in cursor1.fetchall():
            number+=1
            if (el[-1]-el[-2])<5:
                continue
            #print(number)
            el=list(el)
            session=el[6].replace('SESSION:','')
            session=delsession(session,4,1)
            doi=el[3]
            article_url=acm_pre_url_list['article']+doi
            pdf_url=acm_pre_url_list['pdf']+doi
            #authors=';'.join(removeblock(re.split(r'[;]',el[4])))
            #keywords=';'.join(removeblock(re.split(r'[;]',el[7])))
            keywords=el[7]
            insert_data=el[0:2]+[number]+el[2:5]+[session,keywords,article_url,pdf_url]
            cursor2.execute(insert_sql,insert_data)
        conn.commit()
    cursor1.close()
    cursor2.close()
    return
def getpdfurl2(article_url):
    global ndss_pre_url_list
    html=gethtmltext(article_url)
    html=etree.HTML(html)
    all_url=html.xpath('//main/p[@class="ndss_downloads"]/a/@href')
    if len(all_url) is 0:
        return ''
    pdf_url=all_url[0]
    return ndss_pre_url_list['pdf']+pdf_url
def transndssdblp(ndss_table,insert_table):
    global conn
    global ndss_pre_url_list
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select booktitle,year,number,title,authors,block_title,ee from {} '.format(ndss_table)
    insert_sql='insert into {}() values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(insert_table)
    for i in range(1999,2005):
        where_sql="where year={}".format(i)
        cursor1.execute(sel_sql+where_sql)
        number=-1
        for el in cursor1.fetchall():
            number+=1
            if 'Panel' in el[5] or 'Invited talk' in el[5] or el[-1]=='':
                continue
            print(number)
            el=list(el)
            session=el[5]
            session=delsession(session,2,1)
            all_url=el[6]
            pdf_url=getpdfurl2(all_url)
            #authors=';'.join(removeblock(re.split(r'[;]',el[4])))
            #keywords=';'.join(removeblock(re.split(r'[;]',el[7])))
            insert_data=el[0:4]+['']+el[4:5]+[session,'',all_url,pdf_url]
            cursor2.execute(insert_sql,insert_data)
        conn.commit()
    cursor1.close()
    cursor2.close()
    return

def transpredata(pre_table,insert_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select year,number,title,authors,inst_info,session,article_url,pdf_url from {} where conf="USENIX Security" '.format(pre_table)
    insert_sql='insert into {}(conf,year,number,title,authors,inst_info,session,article_url,pdf_url) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'.format(insert_table)
    for i in range(2005,2021):
        where_sql=" and year={}".format(i)
        cursor1.execute(sel_sql+where_sql)
        print(where_sql)
        for el in cursor1.fetchall():
            this_line=['NDSS']+list(el)
            cursor2.execute(insert_sql,this_line)
            conn.commit()
    return
def sametrans(start_table,end_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select * from {}'.format(start_table)
    insert_sql='insert into {}(conf,year,number,title,authors,cross_infer,inst_info,session) values(%s,%s,%s,%s,%s,%s,%s,%s)'.format(end_table)
    for i in range(1980,2005):
        where_sql=" where year={}".format(i)
        print(where_sql)
        cursor1.execute(sel_sql+where_sql)
        for el in cursor1.fetchall():
            cursor2.execute(insert_sql,el)
            conn.commit()
    return

def transinstinfo(from_table,into_table,inst_col,insert_col):
    return 
if __name__=='__main__':
    #genecrossinfer('article_info_ccs')
    #IAC-CNR, Viale del Policlinico, 137, 00161 Rome, Italy;Dip. Scienze Informazione, Univ. di Roma "La Sapienza", 00198 Rome, Italy
    #transccs('article_info_ccs','article_info_ci')
    #transieee('article_info_ieeesp','article_info_ci')
    #transpredata('article_info_nd','article_info_usenix')
    sametrans('all_article_usenix','article_info_usenix')
    conn.close()