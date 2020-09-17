import requests
import re

import pymysql
from lxml import etree
import string

conn = pymysql.connect('localhost', user='root',password='root',database='pylink1',charset='utf8')
cursor = conn.cursor()

pre_url='https://ieeexplore.ieee.org'
sql_str=['ieee sp',2005]


def gethtmltext(url):#以agent为浏览器的形式访问网页,返回源码,参数是某个论文网页或者会议综述网页的url
    try:
        kv ={'user-agent':'Mozilla/5.0'}
        r=requests.get(url,headers=kv)
        r.raise_for_status()
        r.encoding=r.apparent_encoding
        return r.text
    except:
        return 'error'
    return


def getarticleinfo_ieeesp(article_url,session_title,number):
    global conn
    global curosor
    global pre_url
    global sql_str
    
    html=gethtmltext(article_url)
    html=etree.HTML(html)


    insert_sql="insert into ieeesp_article_info(conf_name,year,number,title,all_author,all_info,session_title,keywords,article_url,pdf_url)\
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    info_path='//script[@type="text/javascript"]/text()[starts-with(.,"\nvar body")]'
    #s='//body/div[@id="LayoutWrapper"]/div/div/div/script[@type="text/javascript"]/text()[contains(.,"var body")]'
    #\{"name":"([^",:]*?)","affiliation":\["([^"]*?)"\][^\}]*?\}|\{"name":"([^",:]*?)"[^\}\[\]]*?\}
    ai_re=re.compile(r'\{"name":"([^",:]*?)","affiliation":\["([^"]*?)"\][^\}]*?\}|\{"name":"([^",:]*?)",[^\}\[\]]*?\}')
    #i_re=re.cop
    keyword_re=re.compile(r'\{"type":"IEEE Keywords","kwd":\[(.*?)\]\}')
    each_keyword_re=re.compile(r'"([^"]*?)"')
    pdf_url_re=re.compile(r'"pdfUrl":"([^"]*?)"')

    title_path='//title/text()'
    article_title=html.xpath(title_path)[0]
    #print(article_title)
    info_str=html.xpath(info_path)[0]
    info_str=str(info_str)
    #print(info_str)

    article_title=str(article_title)
    article_title=article_title.replace(' - IEEE Conference Publication','').strip()

    
    all_ai=ai_re.findall(info_str)
    #print(all_ai)
    all_author=[]
    all_inst=[]
    keyword_str=keyword_re.findall(info_str)
    keyword_str=str(keyword_str)
    all_keyword=each_keyword_re.findall(keyword_str)
    all_keyword=';'.join(all_keyword)
    pdf_url=pdf_url_re.findall(info_str)[0]
    pdf_url=pre_url+pdf_url

    for each_pair in all_ai:
        if each_pair[0]=='':
            all_author.append(each_pair[2])
            all_inst.append('')
        else:
            all_author.append(each_pair[0])
            all_inst.append(each_pair[1])

    print(article_title)
    print(all_author)
    print(all_inst)
    print(all_keyword)
    #print(pdf_url)
    
    all_author=';'.join(all_author)
    all_inst=';'.join(all_inst)
    cursor.execute(insert_sql,(sql_str[0],sql_str[1],number,article_title,all_author,all_inst,session_title,all_keyword,article_url,pdf_url))
    conn.commit()
    
    

def crawlconf_dblpieeesp2005(conf_url):
    global cursor
    global conn
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    #brace_rep=re.compile(r'[{}]')
    article_count=-1
    node_count=0
    s_rep=re.compile(r'\s+')

    
    
    session_str='//header/h2'
    article_url='//nav[@class="publ"]/ul/li/div[@class="body"]/ul/li[@class="ee"][1]/a'
    #article_str='//cite'
    print('start crawl page')
    all_node=html.xpath(session_str+'|'+article_url)
    #conf_title=all_node[0].xpath('./span[@class="title"]/text()')
    #print(conf_title)
    print('crawl ok')
    for es in all_node:
        print(es.tag)
        node_count=node_count+1
        #print(es.tag=='a')
        #print(es.tag=='ul')
        if es.tag=='h2':
            session_title=es.text
            session_title=s_rep.sub(' ',session_title).strip()
            #session_title=procsession(session_title)
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='a':
            #if session_title=='':
                #continue
            if 'Introduction' in session_title:
                continue
            if article_count<=-1:
                article_count=article_count+1
                continue
            article_url=es.get('href')
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            print(article_url)
            getarticleinfo_ieeesp(article_url,session_title,article_count)
            
            
            
            article_count=article_count+1
    
            
    #conn.commit()
    
    return
conf_url_dblpieeesp2005='https://dblp.uni-trier.de/db/conf/sp/sp2005.html'
conf_url_dblpieeesp2006='https://dblp.uni-trier.de/db/conf/sp/sp2006.html'
conf_url_dblpieeesp2007='https://dblp.uni-trier.de/db/conf/sp/sp2007.html'
conf_url_dblpieeesp2008='https://dblp.uni-trier.de/db/conf/sp/sp2008.html'
conf_url_dblpieeesp2009='https://dblp.uni-trier.de/db/conf/sp/sp2009.html'
conf_url_dblpieeesp2010='https://dblp.uni-trier.de/db/conf/sp/sp2010.html'
conf_url_dblpieeesp2011='https://dblp.uni-trier.de/db/conf/sp/sp2011.html'
conf_url_dblpieeesp2012='https://dblp.uni-trier.de/db/conf/sp/sp2012.html'
conf_url_dblpieeesp2013='https://dblp.uni-trier.de/db/conf/sp/sp2013.html'
conf_url_dblpieeesp2014='https://dblp.uni-trier.de/db/conf/sp/sp2014.html'
conf_url_dblpieeesp2015='https://dblp.uni-trier.de/db/conf/sp/sp2015.html'
conf_url_dblpieeesp2016='https://dblp.uni-trier.de/db/conf/sp/sp2016.html'
conf_url_dblpieeesp2017='https://dblp.uni-trier.de/db/conf/sp/sp2017.html'
conf_url_dblpieeesp2018='https://dblp.uni-trier.de/db/conf/sp/sp2018.html'
conf_url_dblpieeesp2019='https://dblp.uni-trier.de/db/conf/sp/sp2019.html'
teststr='https://ieeexplore.ieee.org/document/5207633'
#getarticleinfo_ieeesp(teststr,'',1)
'''
sql_str=['ieee sp',2005]
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2005)

sql_str[1]=2006
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2006)

sql_str[1]=2007
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2007)
'''
'''
sql_str[1]=2009
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2009)

sql_str[1]=2010
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2010)

sql_str[1]=2011
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2011)

#2011 26
'''
'''
sql_str[1]=2012
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2012)

sql_str[1]=2014
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2014)

sql_str[1]=2015
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2015)
'''
'''
sql_str[1]=2016
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2016)

sql_str[1]=2017
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2017)

sql_str[1]=2018
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2018)

sql_str[1]=2019
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2019)
'''
'''
sql_str[1]=2008
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2008)
'''
sql_str[1]=2013
crawlconf_dblpieeesp2005(conf_url_dblpieeesp2013)






