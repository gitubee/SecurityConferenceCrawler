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
    kind,session,index_terms,keywords)\
    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"

    s_rep=re.compile(r'\s+')
    num_find=re.compile(r'[0-9]+')
    #fen_rep=re.compile(r'[:;]')
    
    #start find article infos
    all_keywords=html.xpath('//div[@class="tags-widget"]/div[@class="tags-widget__content"]/ul/li/a/@title')
    article_title=html.xpath('//h1[@class="citation__title"]/text()|//h1[@class="citation__title"]//node()/text()')
    article_title=''.join(article_title)
    article_title=s_rep.sub(' ',article_title)
    # page numbers
    page_str=html.xpath('//span[@class="epub-section__pagerange"]/text()')
    first_page=0
    last_page=0
    if len(page_str)>0:
        page_str=page_str[0]
        all_num=num_find.findall(page_str)
        if len(all_num)==1:
            first_page=int(all_num[0])
            last_page=int(all_num[0])
        elif len(all_num)==2:
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
        this_inst=en.xpath('./a/span[@class="loa__author-info"]/span[@class="loa_author_inst"]/p/text()')
        if len(this_inst)>0:
            this_inst=this_inst[0]
            this_inst=s_rep.sub(' ',this_inst).strip()
            this_inst=this_inst.replace(';',',')
        else:
            this_inst=''
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
    
    cursor.execute(insert_sql,(conf_str[0],conf_str[1],number,article_title,article_doi,oa,oii,first_page,last_page,article_kind,session,oit,ok))
    conn.commit()
    return 1


def crawlconf_ccs2003(start_num,conf_url,conf_str):
    global pre_url
    global restart_pos
    global error_file
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    article_count=start_num
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
            ed=ed.strip()
            if len(ed)<17:
                continue
            if article_count<restart_pos:
                article_count+=1
                continue
            ret_num=0
            try:
                print('='*10+'this is '+str(article_count)+' article =========')
                print(ed)
                ret_num=getarticleinfo_ccs(ed,session_title,article_count,conf_str)
            except Exception as e:
                f=open('./'+error_file,'a+')
                f.write('='*30+conf_str[0]+' '+str(conf_str[1])+'\n')
                f.write('#'*30+str(article_count)+'\n')
                f.write(repr(e))
                f.close()
                ret_num=1
            article_count=article_count+ret_num
    # return the article count for the following url of the same conf
    return article_count


def crawlconf_ccs1993(start_num,conf_url,conf_str):
    global pre_url
    global restart_pos
    global error_file
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    article_count=start_num
    # set the xpath find str
    session_node='//div[@class="toc__section"]'
    all_node=html.xpath(session_node)
    #conf_title=all_node[0].xpath('//title/text()')
    #print(conf_title)
    # process each node which contains each session
    for es in all_node:
        # get the article info and save into the mysql database,
        # restart_pos for situation when you need to restart from some article
        all_doi=es.xpath('./div[@class="issue-item-container"]/div/label[@class="checkbox--primary"]/input/@name')
        if len(all_doi)==0:
            continue
        session_title=es.xpath('./div[@class="left-bordered-title section__title"]/text()')
        if len(session_title)>0:
            session_title=session_title[0]
        else:
            session_title=''
        for ed in all_doi:
            ed=ed.strip()
            ret_num=0
            if len(ed)<18:
                continue
            if article_count<restart_pos:
                article_count+=1
                continue
            try:
                print('='*10+'this is '+str(article_count)+' article =========')
                print(ed)
                ret_num=getarticleinfo_ccs(ed,session_title,article_count,conf_str)

            except Exception as e:
                f=open('./'+error_file,'a+')
                f.write('='*30+conf_str[0]+' '+str(conf_str[1])+'\n')
                f.write('#'*30+str(article_count)+'\n')
                f.write(repr(e)+'\n')
                f.close()
                ret_num=1

            article_count=article_count+ret_num
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
    for eb in all_block[11:]:
        conf_name=eb[0].text
        print('='*30)
        print(conf_name)
        start_num=0
        for ei in range(this_year,1978,-1):
            if str(ei) in conf_name:
                this_year=ei
                break
        conf_str[1]=this_year
        
        for ec in conf_abbr_list:
            if ec in conf_name:
                conf_str[0]=ec
        print(conf_str)
        print('='*30)
        for ep in eb[1:]:
            this_url=ep.get('href')
            print(this_url)
            if this_year>=2003:
                start_num=crawlconf_ccs2003(start_num,this_url,conf_str)
            else:
                start_num=crawlconf_ccs1993(start_num,this_url,conf_str)
        this_year=this_year-1
        restart_pos=0
    return

dblp_index_CCS='https://dblp.uni-trier.de/db/conf/ccs/index.html'

restart_pos=0
test_conf_url='http://dl.acm.org/citation.cfm?id=2660267'
test_article_doi1='10.1145/2976749.2978303'
test_article_doi2='10.1145/3243734.3243760'
#crawlconflink(dblp_index_CCS)

conf_url_ccs_11_04=['https://dl.acm.org/doi/proceedings/10.1145/2046707','https://dl.acm.org/doi/proceedings/10.1145/1866307',
'https://dl.acm.org/doi/proceedings/10.1145/1653662','https://dl.acm.org/doi/proceedings/10.1145/1455770',
'https://dl.acm.org/doi/proceedings/10.1145/1315245','https://dl.acm.org/doi/proceedings/10.1145/1180405',
'https://dl.acm.org/doi/proceedings/10.1145/1102120','https://dl.acm.org/doi/proceedings/10.1145/1030083']
this_year=2011
restart_pos=0
for ec in conf_url_ccs_11_04:
    start_num=0
    if this_year==2007 or this_year==2006 or this_year==2004:
        start_num=1
    #crawlconf_ccs2003(start_num,ec,['CCS',this_year])
    this_year=this_year-1
    restart_pos=0
#crawlconf_ccs(30,test_conf_url,['CCS',2019])

error_link='10.1145/1030083.1030093'
#getarticleinfo_ccs(error_link,'SESSION: Access control',35,['CCS',2004])
test_conf_url='https://dl.acm.org/doi/proceedings/10.1145/352600'
crawlconf_ccs1993(0,test_conf_url,['CCS',2000])
cursor.close()
conn.close()
