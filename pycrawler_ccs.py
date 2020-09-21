import requests
import re

import pymysql
from lxml import etree
import string



conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
cursor = conn.cursor()

pre_url='https://dl.acm.org/'
doi_pre_url='https://dl.acm.org/doi/'
sql_str=['ccs',2020]
conf_abbr_list=['CCS']
restart_pos=0
error_file='error_file.txt'



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


def getarticleinfo_ccs(article_doi,session,number,conf_str):
    global conn
    global cursor
    global pre_url
    global doi_pre_url

    article_url=doi_pre_url+article_doi
    html=gethtmltext(article_url)
    html=etree.HTML(html)
    
    #firstly, judge the article kind
    #if article kind is section remove it
    article_kind=html.xpath('//span[@class="issue-heading"]/text()')
    if len(article_kind)==0 or article_kind[0].strip()=='section':
        return 0
    article_kind=article_kind[0]
    #set sql string and re str
    insert_sql="insert into article_info_ccs(conf,year,number,title,doi,authors,inst_info,firstpage,lastpage,\
    kind,session,index_terms,keywords,article_url,pdf_url)\
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    s_rep=re.compile(r'\s+')
    num_find=re.compile(r'[0-9]+')
    #fen_rep=re.compile(r'[:;]')
    
    #start find article infos
    all_keywords=html.xpath('//div[@class="tags-widget"]/div[@class="tags-widget__content"]/ul/li/a/@title')
    article_title=html.xpath('//h1[@class="citation__title"]/text()|//h1[@class="citation__title"]//node()/text()')
    article_title=''.join(article_title)
    article_title=s_rep.sub(' ',article_title)
    # page numbers
    page_str=html.xpath('//span[@class="epub-section__pagerange"]/text()')[0]
    first_page=0
    last_page=0
    all_num=num_find.findall(page_str)
    if len(all_num)==2:
        first_page=int(all_num[0])
        last_page=int(all_num[1])
    #pdf urls
    pdf_url_node=html.xpath('//a[@title="PDF"]/@href')
    pdf_url=''
    if len(pdf_url_node)>0:
        pdf_url=pre_url+pdf_url_node[0]

    all_index_terms=html.xpath('//ol[@class="rlist organizational-chart"]/li/ol//node()/text()')

    #deal the author inst info
    author_info_str='//div[@class="pill-all-authors authors-accordion disable-truncate hidden"]/div[1]/div/ul/li[@class="loa__item"]'
    all_nodes=html.xpath(author_info_str)
    all_authors=[]
    all_inst_infos=[]
    for en in all_nodes:
        this_author=en.xpath('./a/@title')[0]
        this_author=s_rep.sub(' ',this_author).strip()
        this_inst=en.xpath('./a/span[@class="loa__author-info"]/span[@class="loa_author_inst"]/p/text()')[0]
        this_inst=s_rep.sub(' ',this_inst).strip()
        this_inst=this_inst.replace(';',',')
        all_authors.append(this_author)
        all_inst_infos.append(this_inst)
        
    #print some info
    print(article_title)
    print(article_url)
    print(all_authors)
    print(all_inst_infos)
    print(all_keywords)
    #concate data to input database
    ok=';'.join(all_keywords)
    oa=';'.join(all_authors)
    oii=';'.join(all_inst_infos)
    oit=';'.join(all_index_terms)

    cursor.execute(insert_sql,(conf_str[0],conf_str[1],number,article_title,article_doi,oa,oii,first_page,last_page,article_kind,session,oit,ok,article_url,pdf_url))
    conn.commit()
    return 1


def crawlconf_ccs(start_num,conf_url,conf_str):
    global pre_url
    global restart_pos
    global error_file
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    
    article_count=start_num
    node_count=0

    
    # set the xpath find str
    session_node='//div[@class="toc__section accordion-tabbed__tab"]'
    all_node=html.xpath(session_node)
    #conf_title=all_node[0].xpath('//title/text()')
    #print(conf_title)

    # process each node which contains each session
    for es in all_node:
        # get the article info and save into the mysql database,
        # restart_pos for situation when you need to restart from some article
        doi_node=es.xpath('./div/label/input[@type="hidden"]/@value')
        if len(doi_node)==0:
            continue
        doi_str=doi_node[0]
        all_doi=doi_str.split(r',')
        session_title=es.xpath('./a/text()')
        for ed in all_doi:
            print(ed)
            ret_num=0
            if article_count>=restart_pos:
                try:
                    ret_num=getarticleinfo_ccs(ed,session_title,article_count,conf_str)
                
                except Exception as e:
                    f=open('./'+error_file,'a+')
                    f.write('='*30+conf_str[0]+' '+str(conf_str[1])+'\n')
                    f.write('#'*30+str(article_count)+'\n')
                    f.write(repr(e))
                    f.close()
                    ret_num=1
                
            article_count=article_count+ret_num
        node_count=node_count+1
    # return the article count for the following url of the same conf
    return article_count


#stop using this function 
#reserve to crawl the data of dblp
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
            #getarticleinfo_ccs(article_url,session_title,article_count)
            
            
            
            article_count=article_count+1
            
    #conn.commit()
    
    return

def crawlconflink(dblp_index):
    '''
    crawl conf url from the dblp index page
    '''
    global restart_pos
    global conf_abbr_list

    html=gethtmltext(dblp_index)
    html=etree.HTML(html)

    #set the conf xpath str
    conf_node='//header/h2'
    conf_url='//nav[@class="publ"]/ul/li/div[@class="body"]/ul/li[@class="ee"]/a'
    
    all_node=html.xpath(conf_node+'|'+conf_url)

    # split the conf url depending the the year
    all_block=[]
    each_block=[]
    for en in all_node:
        if en.tag=='h2':
            if len(each_block)>1:
                all_block.append(each_block)
            each_block=[en]
        else:
            each_block.append(en)
    if len(each_block)>1:
        all_block.append(each_block)

    #crawl each year's conf data 
    conf_str=['CCS',2020]
    this_year=2020
    start_num=0
    for eb in all_block:
        conf_name=eb[0].text
        print('='*30)
        print(conf_name)
        start_num=0
        for ei in range(this_year,1978,-1):
            if str(ei) in conf_name:
                this_year=ei
                break
        conf_str[1]=this_year
        this_year=this_year-1
        for ec in conf_abbr_list:
            if ec in conf_name:
                conf_str[0]=ec
        print(conf_str)
        print('='*30)
        for ep in eb[1:]:
            this_url=ep.get('href')
            print(this_url)
            start_num=crawlconf_ccs(start_num,this_url,conf_str)
        restart_pos=0
    return

dblp_index_CCS='https://dblp.uni-trier.de/db/conf/ccs/index.html'

test_conf_url='http://dl.acm.org/citation.cfm?id=2660267'
test_article_doi1='10.1145/2976749.2978303'
test_article_doi2='10.1145/3243734.3243760'
#crawlconflink(dblp_index_CCS)
crawlconf_ccs(30,test_conf_url,['CCS',2019])
#getarticleinfo_ccs(test_article_doi1,'test',1,['CCS',1111])


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

sql_str[1]=2019
crawlconf_dblpccs2005(conf_url_dblpccs2019)
'''
cursor.close()
conn.close()
