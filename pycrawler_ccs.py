import requests
import re

import pymysql
from lxml import etree
import string



conn = pymysql.connect('localhost', user='root',password='root',database='pylink1',charset='utf8')
cursor = conn.cursor()

pre_url='https://dl.acm.org/'
sql_str=['ccs',2005]

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





def removeblock(author_list):
    global special_pattern
    re_info=re.compile('\s+')
    new_list=[]
    for es in author_list:
        temp=re_info.sub(' ',es).strip()
        if temp!='':
            new_list.append(temp)
    return new_list


def getarticleinfo_ccs(article_url,session_title,number):
    global conn
    global curosor
    global pre_url
    global sql_str
    html=gethtmltext(article_url)
    html=etree.HTML(html)
    

    author_info_str='//div[@class="pill-all-authors authors-accordion disable-truncate hidden"]/div[1]/div/ul/li[@class="loa__item"]'
    keywords_str='//ol[@class="rlist organizational-chart"]/li/ol'
    pdf_url_str='//a[@title="pdf"]/@href'
    title_str='//h1[@class="citation__title"]/text()'
    insert_sql="insert into ccs_article_info(conf_name,year,number,title,all_author,all_info,session_title,keywords,article_url)\
                values(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    s_rep=re.compile(r'\s+')
    fen_rep=re.compile(r'[:;]')
    all_nodes=html.xpath(author_info_str+'|'+keywords_str)
    all_author=[]
    all_inst_info=[]
    all_keywords=[]
    #pdf_url=html.xpath(pdf_url_str)
    article_title=html.xpath(title_str)
    print(article_title)
    article_title=article_title[0]
    for en in all_nodes:
        #print(en.tag)
        if en.tag=='li':
            
            this_author=en.xpath('./a/@title')[0]
            #print(this_author)
            this_author=s_rep.sub(' ',this_author).strip()
            this_inst=en.xpath('./a/span[@class="loa__author-info"]/span[@class="loa_author_inst"]/p/text()')[0]
            this_inst=fen_rep.sub(',',this_inst)
            this_inst=s_rep.sub(' ',this_inst).strip()
            this_inst=this_inst.replace(';',',')
            all_author.append(this_author)
            all_inst_info.append(this_inst)
        elif en.tag=='ol':
            all_keywords=en.xpath('.//node()/text()')
            all_keywords=removeblock(all_keywords)


    all_keywords=';'.join(all_keywords)
    #print(article_title)
    #print(article_url)
    print(all_author)
    print(all_inst_info)
    #print(all_keywords)



    all_author=';'.join(all_author)
    all_inst_info=';'.join(all_inst_info)
    cursor.execute(insert_sql,(sql_str[0],sql_str[1],number,article_title,all_author,all_inst_info,session_title,all_keywords,article_url))
    conn.commit()
    
            
    
def crawlconf_dblpccs2005(conf_url):
    global cursor
    global conn
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    #brace_rep=re.compile(r'[{}]')
    article_count=0
    node_count=0
    s_rep=re.compile(r'\s+')

    
    
    session_str='//header/h2'
    article_url='//nav[@class="publ"]/ul/li/div[@class="body"]/ul/li[@class="ee"]/a'
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
            if len(session_title)==0:
                continue
            if 'Keynote' in session_title:
                continue
            if 'Poster' in session_title:
                break
            if 'Demo'in session_title:
                break
            if 'Tutorial' in session_title:
                break
            if article_count<=144:
                article_count=article_count+1
                continue
            article_url=es.get('href')
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            #print(article_url)
            getarticleinfo_ccs(article_url,session_title,article_count)
            
            
            
            article_count=article_count+1
            
    #conn.commit()
    
    return


conf_url_dblpccs2005='https://dblp.uni-trier.de/db/conf/ccs/ccs2005.html'
conf_url_dblpccs2006='https://dblp.uni-trier.de/db/conf/ccs/ccs2006.html'
conf_url_dblpccs2007='https://dblp.uni-trier.de/db/conf/ccs/ccs2007.html'
conf_url_dblpccs2008='https://dblp.uni-trier.de/db/conf/ccs/ccs2008.html'
conf_url_dblpccs2009='https://dblp.uni-trier.de/db/conf/ccs/ccs2009.html'
conf_url_dblpccs2010='https://dblp.uni-trier.de/db/conf/ccs/ccs2010.html'
conf_url_dblpccs2011='https://dblp.uni-trier.de/db/conf/ccs/ccs2011.html'
conf_url_dblpccs2012='https://dblp.uni-trier.de/db/conf/ccs/ccs2012.html'
conf_url_dblpccs2013='https://dblp.uni-trier.de/db/conf/ccs/ccs2013.html'
conf_url_dblpccs2014='https://dblp.uni-trier.de/db/conf/ccs/ccs2014.html'
conf_url_dblpccs2015='https://dblp.uni-trier.de/db/conf/ccs/ccs2015.html'
conf_url_dblpccs2016='https://dblp.uni-trier.de/db/conf/ccs/ccs2016.html'
conf_url_dblpccs2017='https://dblp.uni-trier.de/db/conf/ccs/ccs2017.html'
conf_url_dblpccs2018='https://dblp.uni-trier.de/db/conf/ccs/ccs2018.html'
conf_url_dblpccs2019='https://dblp.uni-trier.de/db/conf/ccs/ccs2019.html'

'''
sql_str[1]=2005
crawlconf_dblpccs2005(conf_url_dblpccs2005)

sql_str[1]=2006
crawlconf_dblpccs2005(conf_url_dblpccs2006)
'''
'''
sql_str[1]=2007
crawlconf_dblpccs2005(conf_url_dblpccs2007)

sql_str[1]=2008
crawlconf_dblpccs2005(conf_url_dblpccs2008)

sql_str[1]=2009
crawlconf_dblpccs2005(conf_url_dblpccs2009)
'''
'''
sql_str[1]=2010
crawlconf_dblpccs2005(conf_url_dblpccs2010)

sql_str[1]=2011
crawlconf_dblpccs2005(conf_url_dblpccs2011)
'''
'''
sql_str[1]=2012
crawlconf_dblpccs2005(conf_url_dblpccs2012)
'''
'''
sql_str[1]=2013
crawlconf_dblpccs2005(conf_url_dblpccs2013)
'''
'''
sql_str[1]=2014
crawlconf_dblpccs2005(conf_url_dblpccs2014)

sql_str[1]=2015
crawlconf_dblpccs2005(conf_url_dblpccs2015)
'''
'''
sql_str[1]=2016
crawlconf_dblpccs2005(conf_url_dblpccs2016)

sql_str[1]=2017
crawlconf_dblpccs2005(conf_url_dblpccs2017)
'''
'''
sql_str[1]=2018
crawlconf_dblpccs2005(conf_url_dblpccs2018)
'''
sql_str[1]=2019
crawlconf_dblpccs2005(conf_url_dblpccs2019)

