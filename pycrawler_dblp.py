import requests
import re

import pymysql
from lxml import etree
import string
import xml.etree.ElementTree  as ET

conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
cursor = conn.cursor()

restart_pos=0
conf_abbr_list=['NDSS','AUSCRYPT','ASIACRYPT','CRYPTO','EUROCRYPT']
error_file='./test'

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

def crawlpagexml(dblp_page):
    '''
    crawl the page xml link from the dblp index page
    '''
    html=gethtmltext(dblp_page)
    html=etree.HTML(html)

    #set the conf xpath str
    block_node='//header/h2'
    single_node='//nav[@class="publ"]/ul[1]/li[2]/div[@class="body"]/ul/li[5]/a'
    
    all_node=html.xpath(block_node+'|'+single_node)

    # split the conf url depending the the year
    all_block=[]
    each_block=[]
    for en in all_node:
        #print(en.tag)
        if en.tag=='h2':
            if len(each_block)>0:
                all_block.append(each_block)
            #print(en.text)
            each_block=[en.text]
        elif len(each_block)!=0:
            #print(en.get('href'))
            each_block.append(en.get('href'))
        else:
            each_block=['',en.get('href')]
    if len(each_block)>1:
        all_block.append(each_block)
    
    return all_block

#give an example of read data of xml link
if __name__=='__main__':
    #conf_dblpndss='https://dblp.uni-trier.de/db/conf/ndss/index.html'
    #crawlpagexml(conf_dblpndss)
    '''
    xml_link='https://dblp.uni-trier.de/rec/conf/ccs/2012.xml'
    xml_string=gethtmltext(xml_link)
    xml_tree=ET.fromstring(xml_string)
    #xml_root=xml_tree.xpath('.//node()')
    process_node=xml_tree.findall('.//proceedings')[0]
    print(process_node.get('key'))
    all_sub_node=process_node.findall('./*')
    all_pair=[]
    temp_pair=[]
    for en in all_sub_node:
        etag=str(en.tag)
        valu=str(en.text)
        temp_pair=[etag,valu]
        all_pair.append(temp_pair)
        print(etag+'@'+valu)
    '''
