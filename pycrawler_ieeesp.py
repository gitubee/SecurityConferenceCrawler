import requests
import re

import pymysql
from lxml import etree
import string

conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
cursor = conn.cursor()

pre_url='https://ieeexplore.ieee.org'
restart_pos=0
error_file='C:/Users/jxt/Desktop/SecConf/ieee_error.txt'

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


def excompinst(all_ai_pair):
    each_re=re.compile('"([^"]*)"')
    comp_inst=[]
    all_author=[]
    cross_infer=[]
    for ep in all_ai_pair:
        if len(ep)==0:
            continue
        all_author=ep[0]
        temp_infer=[]
        all_i=each_re.findall(ep[1])
        for epi in all_i:
            find_sign=False
            find_number=len(comp_inst)
            for i in range(len(comp_inst)):
                if epi==comp_inst[i]:
                    find_sign=True
                    find_number=i
                    break
            if not find_sign:
                comp_inst.append(epi)
            temp_infer.append(find_number)
        cross_infer.append(temp_infer)
    return all_author,cross_infer,comp_inst


def getarticleinfo_ieeesp(article_url,session_title,number,conf_str):
    global conn
    global curosor
    global pre_url
    
    html=gethtmltext(article_url)
    html=etree.HTML(html)


    insert_sql="insert into article_info_ieeesp() values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    info_path='//script[@type="text/javascript"]/text()[starts-with(.,"\nvar body")]'
    #s='//body/div[@id="LayoutWrapper"]/div/div/div/script[@type="text/javascript"]/text()[contains(.,"var body")]'
    #\{"name":"([^",:]*?)","affiliation":\["([^"]*?)"\][^\}]*?\}|\{"name":"([^",:]*?)"[^\}\[\]]*?\}
    #\{"name":"([^",:]*?)"(?:,"affiliation":\["([^"]*?)"(?:,"([^"]*?)")*\]){0,1}[^\}]*?\}
    ai_re=re.compile(r'\{"name":"([^",:]*?)",(?:"affiliation":\[([^\]]*)\])?[^\}]*?\}')
    IEEE_keyword_re=re.compile(r'\{"type":"IEEE Keywords","kwd":\[([^\]]*?)\]\}')
    INSPEC_CI_keyword_re=re.compile(r'\{"type":"INSPEC: Controlled Indexing","kwd":\[([^\]]*?)\]\}')
    INSPEC_NCI_keyword_re=re.compile(r'\{"type":"INSPEC: Non-Controlled Indexing","kwd":\[([^\]]*?)\]\}')
    each_keyword_re=re.compile(r'"([^"]*?)"')
    pdf_url_re=re.compile(r'"pdfUrl":"([^"]*?)"')
    page_num_re=re.compile(r'"startPage":"([^"]*?)","endPage":"([^"]*?)"')
    doi_re=re.compile(r'"doi":"([^"]*?)"')
    #isbn_re=re.compile(r'"isbn":\[\{"format":"([^"]*?ISBN)","value":"([^"]*?)","isbnType":""\}(?:,\{"format":"([^"]*?ISBN)","value":"([^"]*?)","isbnType":""\})*?\]')
    #issn_re=re.compile(r'"issn":\[\{"format":"([^"]*?ISSN)","value":"([^"]*?)"\}(?:,\{"format":"([^"]*?ISSN)","value":"([^"]*?)"\})*?\]')
    article_number_re=re.compile(r'"articleNumber":"([0-9]*?)"')


    title_path='//title/text()'
    article_title=html.xpath(title_path)[0]
    article_title=str(article_title)
    article_title=article_title.replace(' - IEEE Conference Publication','').strip()
    
    #get the string that contains the information
    info_str=html.xpath(info_path)[0]
    info_str=str(info_str)
    
    #print(info_str)
    all_ai=ai_re.findall(info_str)
    #print(all_ai)
    print(all_ai)
    all_author,cross_infer,all_comp_inst=excompinst(all_ai)
    #cross_infer,all_comp_inst=compressinst(all_inst)
    cross_infer_str=[]
    for i in cross_infer:
        #if len(i)>1:
            #print('more isnt data')
            #return 1
        temp_str=':'.join(list(map(str,i)))
        cross_infer_str.append(temp_str)
   # return 1
    cross_infer_str=';'.join(cross_infer_str)

    #pdf_url=''
    #pdf_str=pdf_url_re.findall(info_str)
    #if len(pdf_str)>0:
    #    pdf_url=pre_url+pdf_str[0]
    
    start_page=0
    end_page=0
    page_num_str=page_num_re.findall(info_str)
    if len(page_num_str)>0:
        try:
            start_page=int(page_num_str[0][0])
            end_page=int(page_num_str[0][1])
        except:
            return 0
    
    doi=''
    doi_str=doi_re.findall(info_str)
    if len(doi_str)>0:
        doi=doi_str[0]
    
    article_number=''
    article_number_str=article_number_re.findall(info_str)
    if len(article_number_str)>0:
        article_number=article_number_str[0]
    '''
    isbn=['','']
    isbn_str=isbn_re.findall(info_str)
    if len(isbn_str)>0:
        isbn_str=isbn_str[0]
        print(len(isbn_str))
        pair_num=int(len(isbn_str)/2)
        for i in range(pair_num):
            if 'Electronic' in isbn_str[2*i]:
                isbn[1]=isbn_str[2*i+1]
            else:
                isbn[0]=isbn_str[2*i+1]
    
    issn=['','']
    issn_str=issn_re.findall(info_str)
    if len(issn_str)>0:
        issn_str=issn_str[0]
        pair_num=int(len(issn_str)/2)
        for i in range(pair_num):
            if 'Electronic' in issn_str[2*i]:
                issn[1]=issn_str[2*i+1]
            else:
                issn[0]=issn_str[2*i+1]
    '''
    IEEE_keyword_str=IEEE_keyword_re.findall(info_str)
    IEEE_keyword_str=str(IEEE_keyword_str)
    all_IEEE_keyword=each_keyword_re.findall(IEEE_keyword_str)
    
    INSPEC_CI_keyword_str=INSPEC_CI_keyword_re.findall(info_str)
    INSPEC_CI_keyword_str=str(INSPEC_CI_keyword_str)
    all_INSPEC_CI_keyword=each_keyword_re.findall(INSPEC_CI_keyword_str)

    INSPEC_NCI_keyword_str=INSPEC_NCI_keyword_re.findall(info_str)
    INSPEC_NCI_keyword_str=str(INSPEC_NCI_keyword_str)
    all_INSPEC_NCI_keyword=each_keyword_re.findall(INSPEC_NCI_keyword_str)

    
    #print(article_title)
    #print(all_author)
    #print(cross_infer)
    #print(all_comp_inst)
    
    #print(all_IEEE_keyword)
    #print(all_INSPEC_CI_keyword)
    #print(all_INSPEC_NCI_keyword)
    #print(article_number)
    #print(doi)
    #print(pdf_url)
    #print(isbn)
    #print(issn)

    #print(pdf_url)
    
    all_author=';'.join(all_author)
    
    all_comp_inst=';'.join(all_comp_inst)
    all_IEEE_keyword=';'.join(all_IEEE_keyword)
    all_INSPEC_CI_keyword=';'.join(all_INSPEC_CI_keyword)
    all_INSPEC_NCI_keyword=';'.join(all_INSPEC_NCI_keyword)
    
    cursor.execute(insert_sql,(conf_str[0],conf_str[1],article_title,doi,all_author,cross_infer_str,all_comp_inst,session_title,article_number,start_page,end_page,all_IEEE_keyword,all_INSPEC_CI_keyword,all_INSPEC_NCI_keyword))
    conn.commit()
    return 1
    

def crawlconf_dblpieeesp2005(conf_url,conf_str):
    global cursor
    global conn
    global restart_pos
    global error_file
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    #brace_rep=re.compile(r'[{}]')
    article_count=-1
    s_rep=re.compile(r'\s+')

    session_str='//header/h2'
    article_url_str='//nav[@class="publ"]/ul/li/div[@class="body"]/ul/li[@class="ee"][1]/a'
    #article_str='//cite'
    print('start crawl page')
    all_node=html.xpath(session_str+'|'+article_url_str)
    #conf_title=all_node[0].xpath('./span[@class="title"]/text()')
    #print(conf_title)
    print('crawl ok')
    for es in all_node:
        print(es.tag)
        if es.tag=='h2':
            session_title=es.text
            session_title=s_rep.sub(' ',session_title).strip()
            #session_title=procsession(session_title)
            print('######this is new session:'+session_title)
        elif es.tag=='a':
            article_url=es.get('href')
            if 'Introduction' in session_title or ('ieeexplore' not in article_url and 'doi.org' not in article_url):
                print(article_url)
                print('dont read')
                continue
            if article_count<restart_pos:
                article_count=article_count+1
                continue 
            
            print('========this is '+str(article_count)+'  article============')
            print(article_url)
            ret_num=0
            #try:
            ret_num=getarticleinfo_ieeesp(article_url,session_title,article_count,conf_str)
                #print("next")
            '''
            except Exception as e:
                f=open(error_file,'a+')
                f.write('='*30+conf_str[0]+' '+str(conf_str[1])+'\n')
                f.write('#'*30+str(article_count)+'\n')
                f.write(repr(e)+'\n')
                f.close()
            '''
            ret_num=1
            article_count=article_count+ret_num
    return

def crawlconflink(dblp_index):
    '''
    crawl conf url from the dblp index page
    '''
    global restart_pos

    html=gethtmltext(dblp_index)
    html=etree.HTML(html)

    #set the conf xpath str
    conf_node='//header/h2'
    conf_url='//nav[@class="publ"]/ul[1]/li[1]/div[@class="body"]/ul[1]/li[1]/a'
    
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
    conf_str=['IEEE S&P',2020]
    this_year=2020
    start_num=0
    for eb in all_block[2:]:
        conf_name=eb[0].text
        print('='*30)
        print(conf_name)
        start_num=0
        for ei in range(this_year,1978,-1):
            if str(ei) in conf_name:
                this_year=ei
                break
        conf_str[1]=this_year
        
        print(conf_str)
        print('='*30)
        ep=eb[1]
        this_url=ep.get('href')
        print(this_url)
        crawlconf_dblpieeesp2005(this_url,conf_str)
        this_year=this_year-1
        restart_pos=0
    return




if __name__ == '__main__':
    #test_article_link='https://ieeexplore.ieee.org/document/9152763'
    #getarticleinfo_ieeesp(test_article_link,'aaa',1,['ieee',2001])
    conf_url='https://dblp.uni-trier.de/db/conf/sp/sp2020.html'
    dblp_index='https://dblp.uni-trier.de/db/conf/sp/index.html'
    #crawlconf_dblpieeesp2005(conf_url,["IEEE S&P",2020])
    #crawlconflink(dblp_index)
    test_article='https://ieeexplore.ieee.org/document/63866'
    test_article2='https://ieeexplore.ieee.org/document/8418593'
    test_url='https://ieeexplore.ieee.org/document/6234882'
    getarticleinfo_ieeesp(test_article2,'aaa',11110,['ttt',2070])
    




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




