import requests
import re
from bs4 import BeautifulSoup
import pymysql
from lxml import etree

conn = pymysql.connect('localhost', user='root',password='root',database='pylink1',charset='utf8')
cursor = conn.cursor()

start_num=0
have_pdf=True
pre_url='https://rd.springer.com'

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


def getarticleinfo(article_url,pdf_url,session_title,number):
    global conn
    global cursor
    global sql_str
    
    html=gethtmltext(article_url)
    html=etree.HTML(html)

    article_title=html.xpath('/html/head/meta[@name="citation_title"]/@content')[0]
    author_node=html.xpath('//section[@id="authorsandaffiliations"]/div/ul/li')
    inst_node=html.xpath('//section[@id="authorsandaffiliations"]/div/ol/li')
    keywords=html.xpath('//div[@class="KeywordGroup"]/span[@class="Keyword"]/text()')
    
    all_author=[]
    all_author_cross=[]
    all_inst_block=[]


    s_rep=re.compile('\s+')
    email_author_tag=[]
    for each_author in author_node:
        ea_name=each_author.xpath('./span[@itemprop="name"]/text()')[0]
        ea_name=s_rep.sub(' ',ea_name).strip()
        all_author.append(ea_name)
        temp_aff=each_author.xpath('./ul/li/text()')
        temp_cross=[]
        for e in temp_aff:
            numb=int(e)-1
            temp_cross.append(numb)
        all_author_cross.append(temp_cross)
        
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
        all_inst_block.append(temp_block)

    #all_depart=[]
    all_inst=[]
    all_city=[]
    all_country=[]
    for each_ac in all_author_cross:
        #temp_depart=[]
        temp_inst=[]
        temp_city=[]
        temp_country=[]
        for ec in each_ac:
            #temp_depart.append(all_inst_block[ec][0])
            temp_inst.append(all_inst_block[ec][1])
            temp_city.append(all_inst_block[ec][2])
            temp_country.append(all_inst_block[ec][3])
        #temp_depart=':'.join(temp_depart)
        temp_inst=':'.join(temp_inst)
        temp_city=':'.join(temp_city)
        temp_country=':'.join(temp_country)
        #all_depart.append(temp_depart)
        all_inst.append(temp_inst)
        all_city.append(temp_city)
        all_country.append(temp_country)

    #od=';'.join(all_depart)
    oi=';'.join(all_inst)
    oc1=';'.join(all_city)
    oc2=';'.join(all_country)

    block_rep=re.compile(r'^[;:]+$')
    #od=block_rep.sub('',od)
    oa=';'.join(all_author)
    oi=block_rep.sub('',oi)
    oc1=block_rep.sub('',oc1)
    oc2=block_rep.sub('',oc2)
    ok=';'.join(keywords)
    ok=s_rep.sub(' ',ok)
    article_title=s_rep.sub(' ',article_title)
    print(article_title)
    print(all_author)
    #print(all_depart)
    print(all_inst)
    print(all_city)
    print(all_country)
    print(ok)


    
    sql='insert into springer_article_info_lessdata(conf_name,year,number,title,all_author,all_city,all_country,all_inst,session_title,keywords,pdf_url,article_url) \
            values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
    all_author=';'.join(all_author)
    cursor.execute(sql,(sql_str[0],sql_str[1],number,article_title,oa,oc1,oc2,oi,session_title,ok,pdf_url,article_url))
    conn.commit()
    
                
                
            
            
    

def crawlconf_springer2005(conf_url):
    
    global pre_url
    global start_num
    global have_pdf
    
    html=gethtmltext(conf_url)
    html=etree.HTML(html)
    session_title=''
    
    article_count=start_num
    node_count=0
    
    session_str='//li[@class="part-item"]/h3[@class="content-type-list__subheading"]'
    article_str='//li[@class="chapter-item content-type-list__item"]/div/div/a'
    pdf_str='//li[@class="chapter-item content-type-list__item"]/div[@class="content-type-list__action"]/a'
    all_node=html.xpath(session_str+'|'+article_str+'|'+pdf_str)
    #conf_title=all_node[0].xpath('./span[@class="title"]/text()')
    #print(conf_title)

    for es in all_node:
        print(es.tag)
        if es.tag=='h3':
            session_title=''
            session_title=es.text
            article_title=''
            #session_title=procsession2(session_title)
            print('######this is new session:'+session_title+'  node is:'+str(node_count))
        elif es.tag=='a':
            if session_title == 'Invited Talk':
                continue
            node_class=es.get('class')
            if node_class =='content-type-list__link u-interface-link':
                article_title=es.text
                article_url=pre_url+es.get('href')
                print('========this is '+str(article_count)+'  article============'+'  node is:'+str(node_count))
                print(article_title)
                print(article_url)
                pdf_url=''
                if have_pdf:
                      continue
            elif node_class=='content-type-list__action-label test-book-toc-download-link':
                if article_title is '':
                      continue
                pdf_url=pre_url+es.get('href')
                print(pdf_url)
                
            getarticleinfo(article_url,pdf_url,session_title,article_count)
            article_count=article_count+1
            
        node_count=node_count+1
        
    start_num=article_count
    return

    

c_n='asiacrypto'
sql_str=[c_n,2006]
conf_url_ASIACRYPT2005='https://rd.springer.com/book/10.1007/11593447'
conf_url_ASIACRYPT2006='https://rd.springer.com/book/10.1007/11935230'
conf_url_ASIACRYPT2007='https://rd.springer.com/book/10.1007/978-3-540-76900-2'
conf_url_ASIACRYPT2008='https://rd.springer.com/book/10.1007/978-3-540-89255-7'
conf_url_ASIACRYPT2009='https://rd.springer.com/book/10.1007/978-3-642-10366-7'
conf_url_ASIACRYPT2010='https://rd.springer.com/book/10.1007/978-3-642-17373-8'
conf_url_ASIACRYPT2011='https://rd.springer.com/book/10.1007/978-3-642-25385-0'
conf_url_ASIACRYPT2012='https://rd.springer.com/book/10.1007/978-3-642-34961-4'
conf_url_ASIACRYPT2013_1='https://rd.springer.com/book/10.1007/978-3-642-42033-7'
conf_url_ASIACRYPT2013_2='https://rd.springer.com/book/10.1007/978-3-642-42045-0'
conf_url_ASIACRYPT2014_1='https://rd.springer.com/book/10.1007/978-3-662-45611-8'
conf_url_ASIACRYPT2014_2='https://rd.springer.com/book/10.1007/978-3-662-45608-8'
conf_url_ASIACRYPT2015_1='https://rd.springer.com/book/10.1007/978-3-662-48797-6'
conf_url_ASIACRYPT2015_2='https://rd.springer.com/book/10.1007/978-3-662-48800-3'
conf_url_ASIACRYPT2016_1='https://rd.springer.com/book/10.1007/978-3-662-53887-6'
conf_url_ASIACRYPT2016_2='https://rd.springer.com/book/10.1007/978-3-662-53890-6'
conf_url_ASIACRYPT2017_1='https://rd.springer.com/book/10.1007/978-3-319-70694-8'
conf_url_ASIACRYPT2017_2='https://rd.springer.com/book/10.1007/978-3-319-70697-9'
conf_url_ASIACRYPT2017_3='https://rd.springer.com/book/10.1007/978-3-319-70700-6'
conf_url_ASIACRYPT2018_1='https://rd.springer.com/book/10.1007/978-3-030-03326-2'
conf_url_ASIACRYPT2018_2='https://rd.springer.com/book/10.1007/978-3-030-03329-3'
conf_url_ASIACRYPT2018_3='https://rd.springer.com/book/10.1007/978-3-030-03332-3'

conf_url_ASIACRYPT2019_1='https://rd.springer.com/book/10.1007/978-3-030-34578-5'
conf_url_ASIACRYPT2019_2='https://rd.springer.com/book/10.1007/978-3-030-34621-8'
conf_url_ASIACRYPT2019_3='https://rd.springer.com/book/10.1007/978-3-030-34618-8'
#crawlconf_springer2005(conf_url_ASIACRYPT2006)
'''
start_num=0
sql_str[1]=2005
crawlconf_springer2005(conf_url_ASIACRYPT2005)

start_num=0
sql_str[1]=2006
crawlconf_springer2005(conf_url_ASIACRYPT2006)
'''

'''
start_num=0
sql_str[1]=2007
crawlconf_springer2005(conf_url_ASIACRYPT2007)
start_num=0
sql_str[1]=2008
crawlconf_springer2005(conf_url_ASIACRYPT2008)
start_num=0
sql_str[1]=2009
crawlconf_springer2005(conf_url_ASIACRYPT2009)


start_num=0
sql_str[1]=2010
crawlconf_springer2005(conf_url_ASIACRYPT2010)
'''
'''
start_num=0
sql_str[1]=2011
crawlconf_springer2005(conf_url_ASIACRYPT2011)
start_num=0
sql_str[1]=2012
crawlconf_springer2005(conf_url_ASIACRYPT2012)
'''
'''
sql_str[1]=2013
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2013_1)#共27篇

crawlconf_springer2005(conf_url_ASIACRYPT2013_2)
'''
'''
sql_str[1]=2014
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2014_1)#共29篇

crawlconf_springer2005(conf_url_ASIACRYPT2014_2)

sql_str[1]=2015
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2015_1)#共32篇

crawlconf_springer2005(conf_url_ASIACRYPT2015_2)
'''

have_pdf=False
'''
sql_str[1]=2016
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2016_1)
crawlconf_springer2005(conf_url_ASIACRYPT2016_2)
'''
'''
sql_str[1]=2017
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2017_1)
crawlconf_springer2005(conf_url_ASIACRYPT2017_2)
crawlconf_springer2005(conf_url_ASIACRYPT2017_3)

sql_str[1]=2018
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2018_1)
crawlconf_springer2005(conf_url_ASIACRYPT2018_2)
crawlconf_springer2005(conf_url_ASIACRYPT2018_3)
'''
'''
sql_str[1]=2019
start_num=0
crawlconf_springer2005(conf_url_ASIACRYPT2019_1)
crawlconf_springer2005(conf_url_ASIACRYPT2019_2)
crawlconf_springer2005(conf_url_ASIACRYPT2019_3)
'''

conf_url_CRYPT2005='https://rd.springer.com/book/10.1007/11535218'
conf_url_CRYPT2006='https://rd.springer.com/book/10.1007/11818175'
conf_url_CRYPT2007='https://rd.springer.com/book/10.1007/978-3-540-74143-5'
conf_url_CRYPT2008='https://rd.springer.com/book/10.1007/978-3-540-85174-5'
conf_url_CRYPT2009='https://rd.springer.com/book/10.1007/978-3-642-03356-8'
conf_url_CRYPT2010='https://rd.springer.com/book/10.1007/978-3-642-14623-7'
conf_url_CRYPT2011='https://rd.springer.com/book/10.1007/978-3-642-22792-9'
conf_url_CRYPT2012='https://rd.springer.com/book/10.1007/978-3-642-32009-5'
conf_url_CRYPT2013_1='https://rd.springer.com/book/10.1007/978-3-642-40041-4'
conf_url_CRYPT2013_2='https://rd.springer.com/book/10.1007/978-3-642-40084-1'
conf_url_CRYPT2014_1='https://rd.springer.com/book/10.1007/978-3-662-44371-2'
conf_url_CRYPT2014_2='https://rd.springer.com/book/10.1007/978-3-662-44381-1'
conf_url_CRYPT2015_1='https://rd.springer.com/book/10.1007/978-3-662-47989-6'
conf_url_CRYPT2015_2='https://rd.springer.com/book/10.1007/978-3-662-48000-7'
conf_url_CRYPT2016_1='https://rd.springer.com/book/10.1007/978-3-662-53018-4'
conf_url_CRYPT2016_2='https://rd.springer.com/book/10.1007/978-3-662-53008-5'
conf_url_CRYPT2016_3='https://rd.springer.com/book/10.1007/978-3-662-53015-3'
conf_url_CRYPT2017_1='https://rd.springer.com/book/10.1007/978-3-319-63688-7'
conf_url_CRYPT2017_2='https://rd.springer.com/book/10.1007/978-3-319-63715-0'
conf_url_CRYPT2017_3='https://rd.springer.com/book/10.1007/978-3-319-63697-9'
conf_url_CRYPT2018_1='https://rd.springer.com/book/10.1007/978-3-319-96884-1'
conf_url_CRYPT2018_2='https://rd.springer.com/book/10.1007/978-3-319-96881-0'
conf_url_CRYPT2018_3='https://rd.springer.com/book/10.1007/978-3-319-96878-0'
conf_url_CRYPT2019_1='https://rd.springer.com/book/10.1007/978-3-030-26948-7'
conf_url_CRYPT2019_2='https://rd.springer.com/book/10.1007/978-3-030-26951-7'
conf_url_CRYPT2019_3='https://rd.springer.com/book/10.1007/978-3-030-26954-8'

have_pdf=True
sql_str[0]='crypto'

'''
sql_str[1]=2005
start_num=0
crawlconf_springer2005(conf_url_CRYPT2005)
sql_str[1]=2006
start_num=0
crawlconf_springer2005(conf_url_CRYPT2006)
'''
'''
sql_str[1]=2007
start_num=0
crawlconf_springer2005(conf_url_CRYPT2007)

sql_str[1]=2008
start_num=0
crawlconf_springer2005(conf_url_CRYPT2008)

sql_str[1]=2009
start_num=0
crawlconf_springer2005(conf_url_CRYPT2009)
'''
'''
sql_str[1]=2010
start_num=0
crawlconf_springer2005(conf_url_CRYPT2010)

sql_str[1]=2011
start_num=0
crawlconf_springer2005(conf_url_CRYPT2011)

sql_str[1]=2012
start_num=0
crawlconf_springer2005(conf_url_CRYPT2012)
'''
'''
sql_str[1]=2013
start_num=0
crawlconf_springer2005(conf_url_CRYPT2013_1)
crawlconf_springer2005(conf_url_CRYPT2013_2)
'''
'''
sql_str[1]=2014
start_num=0
crawlconf_springer2005(conf_url_CRYPT2014_1)
crawlconf_springer2005(conf_url_CRYPT2014_2)

sql_str[1]=2015
start_num=0
crawlconf_springer2005(conf_url_CRYPT2015_1)
crawlconf_springer2005(conf_url_CRYPT2015_2)
'''

'''
sql_str[1]=2016
start_num=0
crawlconf_springer2005(conf_url_CRYPT2016_1)
crawlconf_springer2005(conf_url_CRYPT2016_2)
crawlconf_springer2005(conf_url_CRYPT2016_3)
'''


have_pdf=False
'''

sql_str[1]=2017
start_num=0
crawlconf_springer2005(conf_url_CRYPT2017_1)
crawlconf_springer2005(conf_url_CRYPT2017_2)
crawlconf_springer2005(conf_url_CRYPT2017_3)


sql_str[1]=2018
start_num=0
crawlconf_springer2005(conf_url_CRYPT2018_1)
crawlconf_springer2005(conf_url_CRYPT2018_2)
crawlconf_springer2005(conf_url_CRYPT2018_3)


sql_str[1]=2019
start_num=0
crawlconf_springer2005(conf_url_CRYPT2019_1)
crawlconf_springer2005(conf_url_CRYPT2019_2)
crawlconf_springer2005(conf_url_CRYPT2019_3)
'''

conf_url_EUROCRYPT2005='https://rd.springer.com/book/10.1007/b136415'
conf_url_EUROCRYPT2006='https://rd.springer.com/book/10.1007/11761679'
conf_url_EUROCRYPT2007='https://rd.springer.com/book/10.1007/978-3-540-72540-4'
conf_url_EUROCRYPT2008='https://rd.springer.com/book/10.1007/978-3-540-78967-3'
conf_url_EUROCRYPT2009='https://rd.springer.com/book/10.1007/978-3-642-01001-9'
conf_url_EUROCRYPT2010='https://rd.springer.com/book/10.1007/978-3-642-13190-5'
conf_url_EUROCRYPT2011='https://rd.springer.com/book/10.1007/978-3-642-20465-4'
conf_url_EUROCRYPT2012='https://rd.springer.com/book/10.1007/978-3-642-29011-4'
conf_url_EUROCRYPT2013='https://rd.springer.com/book/10.1007/978-3-642-38348-9'
conf_url_EUROCRYPT2014='https://rd.springer.com/book/10.1007/978-3-642-55220-5'
conf_url_EUROCRYPT2015_1='https://rd.springer.com/book/10.1007/978-3-662-46800-5'
conf_url_EUROCRYPT2015_2='https://rd.springer.com/book/10.1007/978-3-662-46803-6'
conf_url_EUROCRYPT2016_1='https://rd.springer.com/book/10.1007/978-3-662-49890-3'
conf_url_EUROCRYPT2016_2='https://rd.springer.com/book/10.1007/978-3-662-49896-5'
conf_url_EUROCRYPT2017_1='https://rd.springer.com/book/10.1007/978-3-319-56620-7'
conf_url_EUROCRYPT2017_2='https://rd.springer.com/book/10.1007/978-3-319-56614-6'
conf_url_EUROCRYPT2017_3='https://rd.springer.com/book/10.1007/978-3-319-56617-7'
conf_url_EUROCRYPT2018_1='https://rd.springer.com/book/10.1007/978-3-319-78381-9'
conf_url_EUROCRYPT2018_2='https://rd.springer.com/book/10.1007/978-3-319-78375-8'
conf_url_EUROCRYPT2018_3='https://rd.springer.com/book/10.1007/978-3-319-78372-7'
conf_url_EUROCRYPT2019_1='https://rd.springer.com/book/10.1007/978-3-030-17653-2'
conf_url_EUROCRYPT2019_2='https://rd.springer.com/book/10.1007/978-3-030-17656-3'
conf_url_EUROCRYPT2019_3='https://rd.springer.com/book/10.1007/978-3-030-17659-4'
conf_url_EUROCRYPT2020_1='https://rd.springer.com/book/10.1007/978-3-030-45721-1'
conf_url_EUROCRYPT2020_2='https://rd.springer.com/book/10.1007/978-3-030-45724-2'
conf_url_EUROCRYPT2020_3='https://rd.springer.com/book/10.1007/978-3-030-45727-3'

have_pdf=True
sql_str[0]='eurocrypto'

'''
sql_str[1]=2005
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2005)
sql_str[1]=2006
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2006)
'''
'''
sql_str[1]=2007
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2007)

sql_str[1]=2008
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2008)

sql_str[1]=2009
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2009)
'''

'''
sql_str[1]=2010
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2010)

sql_str[1]=2011
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2011)

sql_str[1]=2012
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2012)
'''
'''
sql_str[1]=2013
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2013)

sql_str[1]=2014
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2014)
'''
'''
sql_str[1]=2015
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2015_1)
crawlconf_springer2005(conf_url_EUROCRYPT2015_2)



sql_str[1]=2016
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2016_1)
crawlconf_springer2005(conf_url_EUROCRYPT2016_2)
'''


'''
sql_str[1]=2017
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2017_1)
crawlconf_springer2005(conf_url_EUROCRYPT2017_2)
crawlconf_springer2005(conf_url_EUROCRYPT2017_3)
'''

have_pdf=False
'''
sql_str[1]=2018
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2018_1)
crawlconf_springer2005(conf_url_EUROCRYPT2018_2)
crawlconf_springer2005(conf_url_EUROCRYPT2018_3)
'''
'''
sql_str[1]=2019
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2019_1)
crawlconf_springer2005(conf_url_EUROCRYPT2019_2)
crawlconf_springer2005(conf_url_EUROCRYPT2019_3)

sql_str[1]=2020
start_num=0
crawlconf_springer2005(conf_url_EUROCRYPT2020_1)
crawlconf_springer2005(conf_url_EUROCRYPT2020_2)
crawlconf_springer2005(conf_url_EUROCRYPT2020_3)
'''
sql_str[0]='crypto'
sql_str[1]=2013
have_pdf=True
start_num=0
crawlconf_springer2005(conf_url_CRYPT2013_1)
crawlconf_springer2005(conf_url_CRYPT2013_2)



conn.close()
cursor.close()
















