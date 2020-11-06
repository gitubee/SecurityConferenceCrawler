import requests
import re
import pymysql
from lxml import etree

conn = pymysql.connect('localhost', user='root',password='root',database='pylink1',charset='utf8')
cursor = conn.cursor()


text = '''
<div>
<ul>
<li class="item-0"><a href="link1.html">first item</a></li>
<li class="item-1"><a href="link2.html">second item</a></li>
<li class="item-inactive"><a href="link3.html">third item</a></li>
<li class="item-1"><a href="link4.html">fourth item</a></li>
<li class="item-0"><a href="link5.html">fifth item</a>
<div><p>Paul Forney, CISSP-ISSAP, CSSLP, CCSP, GREM</p>
<p>test text</p>
</div>
</ul>
</div>
'''
now_conf='none'
pre_url='https://www.ndss-symposium.org'
special_pattern='aaaaaaaaaaaaaaaa'
gn=0

def removeblock(author_list):
    global special_pattern
    re_info=re.compile(r'\s+')
    new_list=[]
    for es in author_list:
        temp=re_info.sub(' ',es).strip()
        if temp!='' and special_pattern not in temp:
            new_list.append(temp)
    return new_list
def delauthorlist2(author_list):
    all_author=[]
    all_institution=[]
    start_pos=0
    author_list=re.split(r'[;]',author_list)
    for es in author_list:
        start_pos=0
        all_part=re.split(r',| and ',es)
        #print(all_part)
        all_part=removeblock(all_part)
        if len(all_part)<2:
            continue;
        for eachs in all_part:
            if 'Universi' in eachs or 'Institut' in eachs or 'Lab' in eachs:
                break
            start_pos=start_pos+1
        if start_pos==len(all_part):
            this_inst=all_part[-1]
            all_part=all_part[:-1]
        else:
            this_inst=','.join(all_part[start_pos:])
            all_part=all_part[:start_pos]
        for ea in all_part:
            all_author.append(ea)
            all_institution.append(this_inst)
    return [all_author,all_institution]

def delauthorlist3(author_list):
    all_author=[]
    all_institution=[]
    author_list=re.split(r'[\)]',author_list)
    for es in author_list:
        all_part=re.split(r'\(',es)
        #print(all_part)
        if len(all_part)<2:
            continue;
        this_inst=all_part[1]
        re_info=re.compile(r'\s+')
        this_inst=re_info.sub(' ',this_inst)
        all_part=re.split(r'[;,]| and|and ',all_part[0])
        all_part=removeblock(all_part)
        for ea in all_part:
            all_author.append(ea)
            all_institution.append(this_inst)
    return [all_author,all_institution]
    

def gethtmltext(url):#以agent为浏览器的形式访问网页,返回源码,参数是某个论文网页或者会议综述网页的url
      try:
            kv ={'user-agent':'Mozilla/5.0'}
            r=requests.get(url,headers=kv)
            r.raise_for_status()
            r.encoding=r.apparent_encoding
            return r.text
      except:
            return 'error'
def procsession2(session_title):
    session_title=session_title.strip()
    end_rep=re.compile(r'[0-9]$|I+$')
    session_title=end_rep.sub('',session_title)
    start_rep=re.compile(r'Session\s*\d+\s*[aAbBcC]?:|SESSION\s*\d*\s*[aAbBcC]?:')
    session_title=start_rep.sub('',session_title)
    session_title=session_title.strip()
    return session_title
def getpdfurl2(article_url):
    global gn
    global pre_url
    html=gethtmltext(article_url)
    #print(article_url)
    html=etree.HTML(html)
    #print(article_url)
    all_url=html.xpath('//main/p[@class="ndss_downloads"]/a/@href')
    #print(all_url)
    if len(all_url) is 0:
        return ''
    pdf_url=all_url[gn]
    #print(pdf_url)
    
    return pre_url+pdf_url

#https://www.ndss-symposium.org/wp-content/uploads/2017/09/Space-Efficient-Block-Storage-Integrity-Alina-Oprea.pdf

def crawlconf_ndss2020(conf_url,sql_str):
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    key_word_string=''
    conf_title=html.xpath('//title/text()')
    session_str='//a[@class="list-group-item list-group-item-warning card-subheading-session"]'
    article_str='//ul[@class="list-group list-group-session card-collapse collapse show"]/li/div[@class="row"]/div[@class="col-10"]'
    pdf_str='//ul[@class="list-group list-group-session card-collapse collapse show"]/li/div[@class="row"]/div[@class="col-2"]'
    print(conf_title)
    article_count=0
    node_count=0
    session_title=''

    print('start py')
    sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url,article_url) \
        values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    all_node=html.xpath(session_str+'|'+article_str+'|'+pdf_str)
    for es in all_node:
        print(es.tag)
        #print(es.tag=='a')
        #print(es.tag=='ul')
        if es.tag=='a':
            session_title=es.xpath('./div/div[@class="col-5"]/text()|./div/div[@class="col-8"]/text()')
            if len(session_title)==0:
                session_title=''
                continue
            session_title=session_title[0]
            session_title=session_title.replace('\n','').strip()
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        else:
            if session_title=='':
                continue
            if 'Keynote' in session_title:
                continue
            if es.get('class')=='col-10':
                article_url=es.xpath('./div[1]/strong/a/@href')[0]
                article_title=es.xpath('./div[1]/strong/a/text()')[0]
                article_author=es.xpath('./div[2]/p/text()')[0]
            else:
                if article_count<=-1:
                    article_count=article_count+1
                    continue
                pdf_url=es.xpath('./div[2]/a/@href')[0]
                print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
                all_author,all_inst=delauthorlist3(article_author)
                print(article_title)
                #print(pdf_url)
                #print(article_url)
                #print(all_author)
                #print(all_inst)
                all_author=';'.join(all_author)
                all_inst=';'.join(all_inst)
                
                cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url,article_url))
                conn.commit()

                article_count=article_count+1
        node_count=node_count+1
                
    return
def crawlconf_ndss2018(conf_url,sql_str):
    global conn
    global cursor
    global pre_url
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    conf_title=html.xpath('//title/text()')
    session_str='//tr[@id]/td[1]/h4'
    article_str='//td[@colspan]/div[@class="row"]'
    print(conf_title)
    all_node=html.xpath(session_str+'|'+article_str)
    
    session_title=''
    node_count=0
    article_count=0

    print('start py')
    sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url) \
        values(%s,%s,%s,%s,%s,%s,%s,%s)'
    
    for es in all_node:
        print(es.tag)
        if es.tag=='h4':
            session_title=es.text
            if len(session_title)==0:
                session_title=''
                continue
            session_title=session_title.replace('\n','').strip()
            
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        else:
            if session_title=='':
                continue
            pdf_url=es.xpath('./div[2]/p/a[1]/@href')[0]
            pdf_url=pre_url+pdf_url
            #print(article_url)
            article_title=es.xpath('./div[1]/p/b/text()')[0]
            #print(article_title)
            author_list=es.xpath('./div[1]/p/text()|div[1]/p/em/text()')
            author_list=''.join(author_list)
            
            
            
            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
            all_author,all_inst=delauthorlist3(author_list)
            article_title=article_title.strip()
            
            print(article_title)
            #print(pdf_url)
            #print(article_url)
            #print(all_author)
            #print(all_inst)
            all_author=';'.join(all_author)
            all_inst=';'.join(all_inst)
                
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url))
            conn.commit()

            article_count=article_count+1
        node_count=node_count+1
        
            
    return


def crawlconf_ndss2012(conf_url,sql_str,format_str):
    global pre_url
    global cursor
    global conn
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    article_count=0
    node_count=0

    now_mode=0
    article_title=''
    
    conf_title=html.xpath('//h1/text()')
    print(conf_title)
    all_node=html.xpath(format_str[0])
    for es in all_node:
        print(es.tag)
        
        if es.tag==format_str[1]:
            now_mode=0
            session_title=es.xpath('./text()')[0]
            #if session_title
            #print(key_word_string)
            session_title=procsession2(session_title)
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag==format_str[2]:
            now_mode=1
            article_url=es.xpath(format_str[4])[0]
            article_url=pre_url+article_url
            pdf_url=getpdfurl2(article_url)
            article_title=es.text
            
        elif es.tag==format_str[3]:
            if now_mode is not 1:
                continue
            else:
                now_mode=0
            authorinst_list=es.text
            #print(authorinst_list)
            all_author=re.split('[,;]| and|and ',authorinst_list)
            all_author=removeblock(all_author)
            if article_title is '':
                continue

            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))

            #print(article_url)
            print(pdf_url)
            print(article_title)
            print(all_author)
            #print(all_inst)

            
            sql='insert into pre_info(conf_name,year,number,title,all_author,session_title,pdf_url,article_url) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            #all_inst=';'.join(all_inst)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,session_title,pdf_url,article_url))
            
            conn.commit()
            
            article_count=article_count+1
            

            
        node_count=node_count+1
    return

def crawlconf_dblqndss2008(conf_url,sql_str):
    global cursor
    global conn
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    
    article_count=0
    node_count=0
    
    session_str='//header/h2'
    article_url='//nav[@class="publ"]/ul/li/div[@class="body"]/ul/li[@class="ee"]/a'
    article_str='//cite'
    all_node=html.xpath(session_str+'|'+article_url+'|'+article_str)
    conf_title=all_node[0].xpath('./span[@class="title"]/text()')
    #print(conf_title)

    
    
    for es in all_node:
        print(es.tag)
        if es.tag=='h2':
            session_title=es.text
            session_title=procsession2(session_title)
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='a':
            article_url=es.get('href')
            #print(article_url)
            pdf_url=getpdfurl2(article_url)
            print(pdf_url)
            
        elif es.tag=='cite':
            article_title=es.xpath('./span[@class="title"]/text()')
            article_title=article_title[0]
            end_rep=re.compile(r'.$')
            article_title=end_rep.sub('',article_title).strip()
            all_author=es.xpath('./span[@itemprop="author"]/a/span/text()')
            #author_url_list=es.xpath('./span[@itemprop="author"]/a/@href')
            all_author=removeblock(all_author)

            if article_title is '' or len(all_author) is 0:
                continue

            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))

            #print(article_url)
            print(pdf_url)
            print(article_title)
            print(all_author)

            '''
            sql='insert into pre_info(conf_name,year,number,title,all_author,session_title,pdf_url,article_url) values(%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,session_title,pdf_url,article_url))

            conn.commit()
            '''
            article_count=article_count+1
            

            
        node_count=node_count+1


            
def crawlconf_ndss2005(conf_url,sql_str,format_str):
    global pre_url
    global cursor
    global conn
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    article_count=0
    node_count=0

    now_mode=0
    article_title=''
    
    conf_title=html.xpath('//h1/text()')
    print(conf_title)
    all_node=html.xpath(format_str[0])
    for es in all_node:
        print(es.tag)
        
        if es.tag==format_str[1]:
            now_mode=0
            session_title=es.xpath('./text()')
            if len(session_title) is 0:
                continue
            #print(key_word_string)
            session_title=procsession2(session_title[0])
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag==format_str[2]:
            now_mode=1
            article_url=es.xpath(format_str[4])[0]
            article_url=pre_url+article_url
            if sql_str[1]==2016:
                pdf_url=article_url
            else:
                pdf_url=getpdfurl2(article_url)
            article_title=es.text
            aritcle_title=removeblock([article_title])[0]
            
        elif es.tag==format_str[3]:
            if now_mode is not 1:
                continue
            else:
                now_mode=0
            if sql_str[1]==2016:
                authorinst_list=''.join(es.xpath(format_str[5]))
            else:
                authorinst_list=es.text
            #print(authorinst_list)
            all_author,all_inst=delauthorlist3(authorinst_list)
            if article_title is '':
                continue

            print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))

            #print(article_url)
            print(pdf_url)
            print(article_title)
            print(all_author)
            print(all_inst)

            
            sql='insert into pre_info(conf_name,year,number,title,all_author,all_inst,session_title,pdf_url,article_url) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            all_author=';'.join(all_author)
            all_inst=';'.join(all_inst)
            cursor.execute(sql,(sql_str[0],sql_str[1],article_count,article_title,all_author,all_inst,session_title,pdf_url,article_url))

            conn.commit()
            
            article_count=article_count+1
            

            
        node_count=node_count+1
    return 

conf_url_ndss2020='https://www.ndss-symposium.org/ndss-program/2020-program/'
conf_url_ndss2019='https://www.ndss-symposium.org/ndss-program/ndss-symposium-2019-program/'
conf_url_ndss2018='https://www.ndss-symposium.org/ndss2018/programme/'
conf_url_ndss2016='https://www.ndss-symposium.org/ndss2016/ndss-2016-programme/'
conf_url_ndss2015='https://www.ndss-symposium.org/ndss2015/ndss-2015-programme/'
conf_url_ndss2014='https://www.ndss-symposium.org/ndss2014/programme/'
conf_url_ndss2013='https://www.ndss-symposium.org/ndss2013/ndss-2013-programme/'
conf_url_ndss2012='https://www.ndss-symposium.org/ndss2012/ndss-2012-programme/'
conf_url_ndss2010='https://www.ndss-symposium.org/ndss2010/'
conf_url_ndss2005='https://www.ndss-symposium.org/ndss2005/'
conf_url_ndss2006='https://www.ndss-symposium.org/ndss2006/'
conf_url_ndss2007='https://www.ndss-symposium.org/ndss2007/'
conf_url_dblqndss2008='https://dblp.uni-trier.de/db/conf/ndss/ndss2008.html'
conf_url_dblqndss2009='https://dblp.uni-trier.de/db/conf/ndss/ndss2009.html'
conf_url_dblqndss2010='https://dblp.uni-trier.de/db/conf/ndss/ndss2010.html'
conf_url_dblqndss2011='https://dblp.uni-trier.de/db/conf/ndss/ndss2011.html'

#test_crawlconfurl()

c_n='NDSS'
session_str2005='/html/body/div[@class]/div[@class]/main/h2'
title_str2005='/html/body/div[@class]/div[@class]/main/h3/a'
author_str2005='/html/body/div[@class]/div[@class]/main/p'
find_str2005=session_str2005+'|'+title_str2005+'|'+author_str2005
url_path2005='./@href'
ai_path2005='./text()'
str_2005=[find_str2005,'h2','a','p',url_path2005,ai_path2005]
 
#crawlconf_ndss2005(conf_url_ndss2005,[c_n,2005],str_2005)
#crawlconf_ndss2005(conf_url_ndss2006,[c_n,2006],str_2005)
#crawlconf_ndss2005(conf_url_ndss2007,[c_n,2007],str_2005)


author_str2012='/html/body/div[@class]/div[@class]/main/div/em'
find_str2012=session_str2005+'|'+title_str2005+'|'+author_str2012
str_2012=[find_str2012,'h2','a','em',url_path2005,ai_path2005]
#crawlconf_ndss2012(conf_url_ndss2012,[c_n,2012],str_2012)


author_str2013='/html/body/div[@class]/div[@class]/main/p/em'
find_str2013=session_str2005+'|'+title_str2005+'|'+author_str2013
str_2013=[find_str2013,'h2','a','p',url_path2005,ai_path2005]
#crawlconf_ndss2012(conf_url_ndss2013,[c_n,2013],str_2013)
#crawlconf_ndss2012(conf_url_ndss2014,[c_n,2014],str_2013)


#crawlconf_ndss2005(conf_url_ndss2015,[c_n,2015],str_2013)


author_str2016='/html/body/div[@class]/div[@class]/main/p/em/..'
title_str2016='/html/body/div[@class]/div[@class]/main/h3/a[1]'
find_str2016=session_str2005+'|'+title_str2016+'|'+author_str2016
ai_path2016='./em/text()'
str_2016=[find_str2016,'h2','a','p',url_path2005,ai_path2016]
#crawlconf_ndss2005(conf_url_ndss2016,[c_n,2016],str_2016)


author_str2017='/html/body/div[@class]/div[@class]/main/p[]'
find_str2017=session_str2005+'|'+title_str2016+'|'+author_str2016
ai_path2016='./em/text()'
str_2016=[find_str2016,'h2','a','p',url_path2005,ai_path2016]
#crawlconf_ndss2005(conf_url_ndss2016,[c_n,2016],str_2016)




#crawlconf_dblqndss2008(conf_url_dblqndss2008,[c_n,2008])
#crawlconf_dblqndss2008(conf_url_dblqndss2009,[c_n,2009])
#crawlconf_dblqndss2008(conf_url_dblqndss2010,[c_n,2010])
#crawlconf_dblqndss2008(conf_url_dblqndss2011,[c_n,2011])

#crawlconf_dblqndss2008(conf_url_dblqndss2013,[c_n,2013])
#crawlconf_dblqndss2008(conf_url_dblqndss2014,[c_n,2014])

#sql_str=['ndss',2020]
#crawlconf_ndss2020(conf_url_ndss2020,sql_str)

sql_str=['ndss',2018]
crawlconf_ndss2018(conf_url_ndss2018,sql_str)
cursor.close()
conn.close()


#test_str='jiaoxiaotong and Angandelos Stavrou, (Columbia University) ; Angelos D. Keromytis, sandiago University; Jason Nieh, Columbia University; Vishal Misra, Columbia University; Dan Rubenstein, Columbia University'
#test_str=re.split(r'[:;]',test_str)

#print(delauthorlist2(test_str))



