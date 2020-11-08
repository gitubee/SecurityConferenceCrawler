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
    single_node='//nav[@class="publ"]/ul/li/div[@class="body"]/ul[3]/li[5]/a'
    
    all_node=html.xpath(block_node+'|'+single_node)

    # split the conf url depending the the year
    all_block=[]
    each_block=[]
    have_block=False
    for en in all_node:
        if en.tag=='h2':
            have_block=True
            if len(each_block)>1:
                all_block.append(each_block)
            each_block=[en]
        elif len(each_block)!=0:
            each_block.append(en)
    if not have_block:
        each_block=['']
        each_block+=all_node
    if len(each_block)>1:
        all_block.append(each_block)
    
    all_output=[]
    temp_block=[]
    #crawl each year's conf data 
    for eb in all_block:
        if eb[0]!='':
            temp_block=[eb[0].text]
        else:
            temp_block=['']
        for ep in eb[1:]:
            this_xml=ep.get('href')
        temp_block.append(this_xml)
        all_output.append(temp_block)
    return all_output

#give an example of read data of xml link
if __name__=='__main__':
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
    
