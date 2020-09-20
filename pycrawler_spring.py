import requests
import re
import pymysql
from lxml import etree

conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
cursor = conn.cursor()


conf_abbr_list=['AUSCRYPT','ASIACRYPT','CRYPTO','EUROCRYPT']
restart_pos=0
pre_url='https://rd.springer.com'
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

'''
<section id="authorsandaffiliations" class="Section1 RenderAsSection1">
    <h2 class="Heading">Authors and Affiliations</h2>
    <div class="content authors-affiliations u-interface">
        <ul class="test-contributor-names">
            <li itemscope="" itemtype="http://schema.org/Person" class="u-mb-2 u-pt-4 u-pb-4">
                <span itemprop="name" class="authors-affiliations__name">Pascal Paillier</span>
                <ul class="authors-affiliations__indexes u-inline-list" data-role="AuthorsIndexes">
                    <li data-affiliation="affiliation-1">1</li>
                </ul>
            </li>
            <li itemscope="" itemtype="http://schema.org/Person" class="u-mb-2 u-pt-4 u-pb-4">
                <span itemprop="name" class="authors-affiliations__name">Damien Vergnaud</span>
                <ul class="authors-affiliations__indexes u-inline-list" data-role="AuthorsIndexes">
                    <li data-affiliation="affiliation-2">2</li>
                </ul>
            </li>
        </ul>
    <ol class="test-affiliations">
        <li class="affiliation" data-test="affiliation-1" data-affiliation-highlight="affiliation-1" itemscope="" itemtype="http://schema.org/Organization">
            <span class="affiliation__count">1.</span>
            <span class="affiliation__item">
                <span itemprop="department" class="affiliation__department">Gemplus Card International</span>
                <span itemprop="name" class="affiliation__name">Advanced Cryptographic Services</span>
                <span itemprop="address" itemscope="" itemtype="http://schema.org/PostalAddress" class="affiliation__address">
                    <span itemprop="addressRegion" class="affiliation__city">Issy-les-Moulineaux</span>
                    <span itemprop="addressCountry" class="affiliation__country">France</span>
                </span>
            </span>
        </li>
        <li class="affiliation" data-test="affiliation-2" data-affiliation-highlight="affiliation-2" itemscope="" itemtype="http://schema.org/Organization">
            <span class="affiliation__count">2.</span>
            <span class="affiliation__item">
                <span itemprop="department" class="affiliation__department">Laboratoire de Mathématiques Nicolas Oresme</span>
                <span itemprop="name" class="affiliation__name">Université de Caen</span>
                <span itemprop="address" itemscope="" itemtype="http://schema.org/PostalAddress" class="affiliation__address">
                    <span itemprop="addressRegion" class="affiliation__city">Caen</span>
                    <span itemprop="addressCountry" class="affiliation__country">France</span>
                </span>
            </span>
        </li>
    </ol>
</div>
</section>
'''


def getarticleinfo(article_url,session,number,conf_str):
    global conn
    global cursor
    
    html=gethtmltext(article_url)
    html=etree.HTML(html)

    article_title=html.xpath('//h1/text()|//h1//node()/text()')
    article_title=''.join(article_title)
    keywords=html.xpath('//div[@class="KeywordGroup"]/span[@class="Keyword"]/text()')
    first_page=html.xpath('/html/head/meta[@name="citation_firstpage"]')[0]
    last_page=html.xpath('/html/head/meta[@name="citation_lastpage"]')[0]
    first_page=int(first_page.get('content'))
    last_page=int(last_page.get('content'))
    pdf_node=html.xpath('/html/head/meta[@name="citation_pdf_url"]')
    pdf_url=''
    if len(pdf_node)>0:
        pdf_url=pdf_node[0].get('content')
    doi=html.xpath('/html/head/meta[@name="citation_doi"]')[0]
    doi=doi.get('content').strip()
    citation_num=html.xpath('//div[@class="main-context__column"]/ul[@id="book-metrics"]/li[1]/a/span[@id="chaptercitations-count-number"]/text()')
    citation_count=0
    '''
    if len(citation_num)>0:
        citation_count=int(citation_num[0].strip())
        '''
    
    author_node=html.xpath('//section[@id="authorsandaffiliations"]/div/ul/li')
    inst_node=html.xpath('//section[@id="authorsandaffiliations"]/div/ol/li')
    all_author=[]
    all_author_cross=[]
    email_author_tag=[]
    #all_depart=[]
    all_inst=[]
    all_city=[]
    all_country=[]
    # get the citation number
    

    # get the author name and cross infer list
    s_rep=re.compile(r'\s+')

    for each_author in author_node:
        ea_name=each_author.xpath('./span[@itemprop="name"]/text()')[0]
        ea_name=s_rep.sub(' ',ea_name).strip()
        all_author.append(ea_name)
        temp_aff=each_author.xpath('./ul/li/text()')
        temp_cross=[]
        for e in temp_aff:
            numb=e.strip()
            temp_cross.append(numb)
        temp_cross=':'.join(temp_cross)
        all_author_cross.append(temp_cross)
        this_email_tag='0'
        email_node=each_author.xpath('./span[@class="author-information"]')
        if len(email_node)>0:
            this_email_tag='1'
        email_author_tag.append(this_email_tag)
        
    
    #get the inst info
    for each_inst in inst_node:
        temp_block=['','','','']
        all_span=each_inst.xpath('./span/span|./span/span/span')
        for es in all_span:
            this_text=es.text
            #print(this_text)
            if this_text:
                  this_text=s_rep.sub(' ',this_text)
                  this_text=this_text.strip()
            else:
                  continue
            span_kind=es.get('itemprop')
            #if span_kind =='department':
                #temp_block[0]=this_text
            if span_kind =='name':
                temp_block[1]=this_text
            elif span_kind=='addressRegion':
                temp_block[2]=this_text
            elif span_kind=='addressCountry':
                temp_block[3]=this_text
        all_inst.append(temp_block[1])
        all_city.append(temp_block[2])
        all_country.append(temp_block[3])

    #concate the data to input the database
    #od=';'.join(all_depart)
    oi=';'.join(all_inst)
    oc1=';'.join(all_city)
    oc2=';'.join(all_country)
    oac=';'.join(all_author_cross)
    oet=';'.join(email_author_tag)

    #od=block_rep.sub('',od)
    oa=';'.join(all_author)
    ok=';'.join(keywords)
    ok=s_rep.sub(' ',ok).strip()
    article_title=s_rep.sub(' ',article_title).strip()
    print(article_title)
    print(all_author)
    #print(all_depart)
    #print(all_inst)
    #print(all_city)
    #print(all_country)
    #print(ok)
    print(pdf_url)

    
    sql='insert into article_info_springer(conf,year,number,title,doi,authors,email_tag,session,\
        cross_infer,insts,citys,countrys,firstpage,lastpage,keywords,citation,pdf_url,article_url) \
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    cursor.execute(sql,(conf_str[0],conf_str[1],number,article_title,doi,oa,oet,session,oac,oi,oc1,oc2,first_page,last_page,ok,citation_count,pdf_url,article_url))
    conn.commit()
    return


def crawlconf_springer2005(start_num,conf_url,conf_str):
    
    global pre_url
    global restart_pos
    global error_file
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    
    article_count=start_num
    node_count=0
    
    # set the xpath find str
    session_str='//li[@class="part-item"]/h3[@class="content-type-list__subheading"]'
    article_str='//li[@class="chapter-item content-type-list__item"]/div/div/a[@class="content-type-list__link u-interface-link"]'
    #pdf_str='//li[@class="chapter-item content-type-list__item"]/div[@class="content-type-list__action"]/a'
    all_node=html.xpath(session_str+'|'+article_str)
    #conf_title=all_node[0].xpath('./span[@class="title"]/text()')
    #print(conf_title)

    # process each node
    for es in all_node:
        print(es.tag)
        if es.tag=='h3':
            # h3 node is the session node
            session_title=''
            session_title=es.text
            if session_title=='':
                continue
            article_title=''
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='a':
            # a kind node is the article info node
            
            article_title=es.text
            article_url=pre_url+es.get('href')
            print('===this is '+str(article_count)+'  article====='+'  node is:'+str(node_count))
            print(article_title)
            print(article_url)
            # get the article info and save into the mysql database,
            # restart_pos for situation when you need to restart from some article 
            if article_count>=restart_pos:
                try:
                    getarticleinfo(article_url,session_title,article_count,conf_str)
                except Exception as e:
                    f=open('./'+error_file,'r+')
                    f.write('='*30+conf_str[0]+' '+str(conf_str[1])+'\n')
                    f.write('#'*30+str(article_count)+'\n')
                    f.write(repr(e))
                    f.close()
            article_count=article_count+1
            
        node_count=node_count+1
    # return the article count for the following url of the same conf
    return article_count


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
    conf_str=['CRYPT',2020]
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
            start_num=crawlconf_springer2005(start_num,this_url,conf_str)
        restart_pos=0
    return
    
restart_pos=0
dblp_index_ASIACRYPT='https://dblp.uni-trier.de/db/conf/asiacrypt/index.html'
dblp_index_EUROCRYPT='https://dblp.uni-trier.de/db/conf/eurocrypt/index.html'
dblp_index_CRYPT='https://dblp.uni-trier.de/db/conf/crypto/index.html'

crawlconflink(dblp_index_CRYPT)
#crawlconf_springer2005(0,'https://link.springer.com/book/10.1007%2F978-3-030-34578-5',['ASIACRYPT',2019])
#getarticleinfo(r'https://link.springer.com/chapter/10.1007/3-540-39568-7_5','Public Key Cryptosystems and Signatures',4,['CRYPTO',1984])


conn.close()
cursor.close()
















