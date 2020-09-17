import requests
import re
#from bs4 import BeautifulSoup
import pymysql
from lxml import etree
import string

special_pattern='Awarded '
conn = pymysql.connect('localhost', user='root',password='root',database='pylink1',charset='utf8')
cursor = conn.cursor()

    
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
        if temp!='' and special_pattern not in temp:
            new_list.append(temp)
    return new_list
def procsession(session_title):
    session_title=session_title.replace('\n','').strip()
    end_rep=re.compile(r'[0-9]$|I+$')
    session_title=end_rep.sub('',session_title)
    session_title=re.split(r'\+|&|:',session_title)
    session_title=';'.join(session_title)
    return session_title
def delauthorlist1(author_list): # 处理第一种情况下的author和institution
    s=0
    e=0
    #print(author_list)
    author_name=author_list[0::2]
    inst_name=author_list[1::2]
    all_author=[]
    all_institution=[]
    if len(author_name)!=len(inst_name):
        return [[],[]]
    for i in range(0,len(author_name)):
        all_as=re.split(r'[,;]|and | and',author_name[i])
        for ea in all_as:
            temp=ea.strip()
            if temp!='':
                all_author.append(temp)
                e=e+1
        this_inst=re.split(r'[;]',inst_name[i])[0]
        for j in range(s,e):
            all_institution.append(this_inst)
        s=e
    return [all_author,all_institution]
def gettimeinf(title_str):
    months=['January','February','March','April','May','June','July','August','September','October','November','December']
    num_format='\d+'
    pos1=-1
    month_save=[]
    
    for i in months:
        if title_str.find(i)>=0:
            month_save.append(i)
    all_num=re.findall(r'\d+',title_str)
    print(all_num)
    if len(month_save)==1:
        return [all_num[-1],month_save[0],all_num[-3],month_save[0],all_num[-2]]
    elif len(month_save)==2:
        return [all_num[-1],month_save[0],all_num[-3],month_save[1],all_num[-2]]
    return    

def getpdfurl1(pre_url,article_url):
    html=gethtmltext(article_url)
    #print(article_url)
    html=etree.HTML(html)
    #print(article_url)
    all_url=html.xpath('//li/a/@href')
    #print(all_url)
    
    for i in all_url:
        if i.endswith('.pdf'):
            pdf_url=i
    #print(pdf_url)
    
    return pre_url+pdf_url

def getarticleinfo_USENIX(article_url):
    html=gethtmltext(article_url)
    html=etree.HTML(html)
    article_title=html.xpath('//head/meta[@name="citation_title"]/@content')
    all_author=html.xpath('//head/meta[@name="citation_author"]/@content')
    all_inst=html.xpath('//head/meta[@name="citation_author_institution"]/@content')
    pdf_url=html.xpath('//head/meta[@name="citation_pdf_url"]/@content')
    return article_title,all_author,all_inst,pdf_url


def crawlconf_dblpUSENIX2012(conf_url,sql_str):
    global cursor
    global conn
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    brace_rep=re.compile(r'[{}]')
    article_count=48
    node_count=0
    
    session_str='//header/h2'
    article_url='//nav[@class="publ"]/ul/li/div[@class="body"]/ul/li[@class="ee"]/a'
    #article_str='//cite'
    all_node=html.xpath(session_str+'|'+article_url)
    #conf_title=all_node[0].xpath('./span[@class="title"]/text()')
    #print(conf_title)

    
    
    for es in all_node:
        print(es.tag)
        node_count=node_count+1
        #print(es.tag=='a')
        #print(es.tag=='ul')
        if es.tag=='h2':
            session_title=es.text
            session_title=procsession(session_title)
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='a':
            article_url=es.get('href')
            #print(article_url)
            article_title,all_author,all_inst,pdf_url=getarticleinfo_USENIX(article_url)
            if len(article_title) is 0:
                continue
            
            article_title=article_title[0]
            article_title=brace_rep.sub('',article_title)
            pdf_url=pdf_url[0]
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            
            
            print(article_title)
            print(all_author)
            print(all_inst)
            print(pdf_url)
            
            sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url,article_url) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            all_inst=';'.join(all_inst)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url,article_url))
            conn.commit()
            
            article_count=article_count+1
            
        '''
        elif es.tag=='cite':
            article_title=es.xpath('./span[@class="title"]/text()')
            print(article_title)
            author_list=es.xpath('./span[@itemprop="author"]/a/span/text()')
            author_url_list=es.xpath('./span[@itemprop="author"]/a/@href')
            print(author_list)
            print(author_url_list)
            '''
        
    return
def crawlconf_USENIX2011(conf_url,sql_str,format_str):
    global cursor
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    article_count=0
    node_count=0
    
    all_node=html.xpath(format_str[0])
    for es in all_node:
        print(es.tag)
        node_count=node_count+1
        if es.tag=='p' and es.get('class')==format_str[1]:
            session_str=es.xpath('./text()')
            session_title=' '.join(removeblock(session_str))
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='p'and es.get('class')==format_str[2]:
            all_article=es.xpath('./b/text()|./b/node()/text()')
            article_title=' '.join(removeblock(all_article))
            all_str=es.xpath(format_str[3])
            all_str=removeblock(all_str)
            #print(all_str)
            #print(all_str)
            all_author,all_inst=delauthorlist1(all_str)
        elif es.tag=='a':
            article_url=es.get('href')
            if not article_url.endswith('.pdf'):
                continue
            pdf_url=conf_url+article_url
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            
            print(pdf_url)
            print(article_title)
            print(all_author)
            print(all_inst)
            
            sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            all_inst=';'.join(all_inst)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url))
            
            article_count=article_count+1
    return
def crawlconf_USENIX2008(conf_url,sql_str,format_str):
    global cursor
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    article_count=0
    node_count=0
    
    all_node=html.xpath(format_str[0])
    for es in all_node:
        print(es.tag)
        node_count=node_count+1
        if es.tag=='p' and es.get('class')==format_str[1]:
            session_title=es.text
            if session_title:
                print('######this is new session:'+session_title+'  node is:'+str(node_count))
            else:
                print('######this is new session:')
                session_title=''
        elif es.tag=='p'and es.get('class')==format_str[2]:
            all_str=es.xpath(format_str[3])
            all_str=removeblock(all_str)
            #print(all_str)
            article_title=all_str[0]
            #print(all_str)
            all_author,all_inst=delauthorlist1(all_str[1:])
        elif es.tag=='a':
            article_url=es.get('href')
            if not article_url.endswith('.pdf'):
                continue
            pdf_url=conf_url+article_url
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            
            print(pdf_url)
            print(article_title)
            print(all_author)
            print(all_inst)
            '''
            sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            all_inst=';'.join(all_inst)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url))
            '''
            article_count=article_count+1
    return

def crawlconf_USENIX2005(conf_url,pre_url,sql_str,format_str):
    global cursor
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    all_session=html.xpath(format_str[0])
    article_count=0
    node_count=0
    session_title=''
    print("all_session:")
    #print(all_session)
    for es in all_session:
        #print(es.tag)
        node_count=node_count+1
        if es.tag=='b':
            session_title=es.text
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='p':
            article_url=es.xpath(format_str[1])
            if article_url==[] or (not article_url[0].endswith('.html')):
                continue
            article_url=article_url[0]
            pdf_url=getpdfurl1(pre_url,pre_url+article_url)
            all_str=es.xpath(format_str[2])
            all_str=removeblock(all_str)
            article_title=all_str[0]
            all_author,all_inst=delauthorlist1(all_str[1:])
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            
            print(pdf_url)
            print(article_title)
            print(all_author)
            print(all_inst)

            sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            all_inst=';'.join(all_inst)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url))
            
            article_count=article_count+1
            
            
    return
            
    




conf_url_dblp_usenix2008='https://dblp.uni-trier.de/db/conf/uss/uss2008.html'
conf_url_usenix2005='https://www.usenix.org/legacy/events/sec05/tech/'
conf_url_usenix2006='https://www.usenix.org/legacy/events/sec06/tech/'
conf_url_usenix2007='https://www.usenix.org/legacy/events/sec07/tech/tech.html'
conf_url_usenix2008='https://www.usenix.org/legacy/events/sec08/tech/'
conf_url_usenix2009='https://www.usenix.org/legacy/events/sec09/tech/'
conf_url_usenix2010='https://www.usenix.org/legacy/events/sec10/tech/'
conf_url_usenix2011='https://www.usenix.org/legacy/events/sec11/tech/'
conf_url_dblqusenix2012='https://dblp.uni-trier.de/db/conf/uss/uss2012.html'
conf_url_dblqusenix2013='https://dblp.uni-trier.de/db/conf/uss/uss2013.html'
conf_url_dblqusenix2014='https://dblp.uni-trier.de/db/conf/uss/uss2014.html'
conf_url_dblqusenix2015='https://dblp.uni-trier.de/db/conf/uss/uss2015.html'
conf_url_dblqusenix2016='https://dblp.uni-trier.de/db/conf/uss/uss2016.html'
conf_url_dblqusenix2017='https://dblp.uni-trier.de/db/conf/uss/uss2017.html'
conf_url_dblqusenix2018='https://dblp.uni-trier.de/db/conf/uss/uss2018.html'
conf_url_dblqusenix2019='https://dblp.uni-trier.de/db/conf/uss/uss2019.html'
#crawlconf_USENIX2008(conf_url_usenix2008)
#conf_title='Proceedings of the 22th USENIX Security Symposium, Washington, DC, USA, August 14-16, 2013'
#print(gettimeinf(conf_title))

#USENIX security 2005 2006 2007
c_n="USENIX Security"
session_str2005='//tr/td[1][@width="50%"]/p[1]/font/b'
article_str2005='//tr/td[1][@width="50%"]/p[position()>1]'
url_str2005='./a/@href|./b/a/@href'
ai_str2005='./a/b/text()|./b/a/text()|./i/text()|./text()'
str_2005=[session_str2005+'|'+article_str2005,url_str2005,ai_str2005]
pre_url_usenix2007='https://www.usenix.org/legacy/events/sec07/tech/'
#crawlconf_USENIX2005(conf_url_usenix2005,conf_url_usenix2005,[c_n,2005],str_2005)
#crawlconf_USENIX2005(conf_url_usenix2006,conf_url_usenix2006,[c_n,2006],str_2005)
#crawlconf_USENIX2005(conf_url_usenix2007,pre_url_usenix2007,[c_n,2007],str_2005)

#getpdfurl1('','https://www.usenix.org/legacy/events/sec05/tech/bono.html')


#USENIX security 2008 2009 2010 2011 2012
#2008
session_str2008='//tr/td[1][@width="50%"]/a/p[@class="techtitle"]'
article_str2008='//tr/td[1][@width="50%"]/p[@class="techdesc"]/i/..'
url_str2008='//tr/td[1][@width="50%"]/p[@class="paperfiles"]/a[2]'
comp_1str2008='techtitle'
comp_2str2008='techdesc'
ai_str2008='./b/text()|./text()|./i/text()'
str_2008=[session_str2008+'|'+article_str2008+'|'+url_str2008,comp_1str2008,comp_2str2008,ai_str2008]
#crawlconf_USENIX2008(conf_url_usenix2008,[c_n,2008],str_2008)

#2009
session_str2009='//tr/td[1][@width="50%"]/p[@class="techtitle"]'
url_str2009='//tr/td[1][@width="50%"]/p[@class="paperfiles"]/a[1]'
ai_str='./b/text()|./text()|./i/text()'
str_2009=[session_str2009+'|'+article_str2008+'|'+url_str2009,comp_1str2008,comp_2str2008,ai_str2008]
#crawlconf_USENIX2008(conf_url_usenix2009,[c_n,2009],str_2009)

#2010
session_str2010='//tr/td[1][@width="50%"]/p[@class="techtitle"]'
article_str2010='//tr/td[1][@width="50%"]/p[@class="fullpaper1"]'
url_str2010='//tr/td[1][@width="50%"]/p[@class="abs"]/b/a[2]'
comp_2str2010='fullpaper1'
str_2010=[session_str2010+'|'+article_str2010+'|'+url_str2010,comp_1str2008,comp_2str2010,ai_str2008]
#crawlconf_USENIX2008(conf_url_usenix2010,[c_n,2010],str_2010)

url_str2011='//tr/td[1][@width="50%"]/p[@class="abs"]/b/a[1]'
ai_str2011='./text()|./i/text()'
str_2011=[session_str2010+'|'+article_str2010+'|'+url_str2011,comp_1str2008,comp_2str2010,ai_str2011]
#crawlconf_USENIX2011(conf_url_usenix2011,[c_n,2011],str_2011)

#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2012,[c_n,2012])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2013,[c_n,2013])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2014,[c_n,2014])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2015,[c_n,2015])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2016,[c_n,2016])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2017,[c_n,2017])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2018,[c_n,2018])
crawlconf_dblpUSENIX2012(conf_url_dblqusenix2019,[c_n,2019])
#crawlconf_dblpUSENIX2012(conf_url_dblqusenix2020,[c_n,2020])
#print(procsession('''Security:aaaII'''))

cursor.close()
conn.close()

#crawlconf_USENIX2005(conf_url_usenix2005,str_2005)


#test_list=['\n\n\n\t ',' ',' a \n\t b \t ','\tab\n']
#print(removeblock(test_list))

#print(removeblock(['a    \nb']))









