from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LTChar,LTTextLine,LTTextBox,LTFigure,LAParams,LTTextBoxHorizontal
from pdfminer.converter import PDFPageAggregator
from pdfminer.high_level import extract_text,extract_pages
from urllib.request import urlopen,Request
from io import StringIO,BytesIO
import re

'''
使用pip命令安装pdfminer.six
'''

shift=0.5                                                #用于确定ltchar 分割的超参数
author_inst_end=False
file_point=None
read_mod=0
author_inst_line=''



def readmail(mail_str):
    mail_str=mail_str.strip()
    s_str=re.split(r'@',mail_str)
    name_str=re.split(r'{},',s_str[0])
    out_list=[]
    for i in name_str:
        out_list.append(i+'@'+s_str[1])
    return out_list


def extractblock(pdf_str,article_title,author_list):

    #首先替换所有的cid;num格式的字符
    all_cid=re.findall(r'\(cid:(\d+)\)',pdf_str)
    all_cid=list(set(all_cid))
    base_num=9
    if len(all_cid)>9:
        print("too much cid:num,is this the right str?")
    else:
        for i in all_cid:
            pdf_str=pdf_str.replace('(cid:'+i+')',str(base_num))
            base_num=base_num-1
    
    all_line=re.split(r'\n',pdf_str)
    print(all_line)
    
    '''
    all_line_temp=[]
    for i in all_line:
        temp=i.strip()
        if i is '':
            continue
        all_line_temp.append(i)
    all_line=all_line_temp
    '''
    
    #提取有作者的所有行
    #同时提取所有包含机构，城市，国家，街道，邮箱的所有行
    pdf_title=''
    temp_author_block=''
    cont_sign=False
    sign=False
    author_sign=False
    all_line_record=[]
    all_inst_line=[]
    all_author_line=[]
    #all_mail_line=[]

    for i in range(len(all_line)):
        sign=False
        if all_line[i] in article_title:
            all_inst_line.append('')
            pdf_title=pdf_title+' '+all_line[i]
            all_line_record.append(0)
            continue
        #判断是否包含作者，是则设置sign为true，标题段关闭
        for ea in author_list:
            if ea in all_line[i]:
                sign=True
                author_sign=True
                break
        #如果这一行包含作者，判断是否连续，连续则连接起来
        if sign:
            if not cont_sign:
                temp_author_block=all_line[i]
            else:
                temp_author_block=temp_author_block+','+all_line[i]
            cont_sign=True
            all_inst_line.append('')
            all_line_record.append(1)
            #如果不是作者，则应该是机构或者标题段
        else:
            #连续标记同时记录上一行的类型，如果为作者行，则将作者串填入作者块
            if cont_sign:
                cont_sign=False
                all_author_line.append(temp_author_block)
                temp_author_block=''
            if author_sign:
                all_inst_line.append(all_line[i])
                all_line_record.append(2)
            else:
                pdf_title=pdf_title+' '+all_line[i]
                all_line_record.append(0)
    #将未塞入作者块的放进去
    if cont_sign:
        cont_sign=False
        all_author_line.append(temp_author_block)
    pdf_title=pdf_title.strip()
    #提取pdf中所有作者，并根据爬取的作者信息判断pdf中作者机构的链接方式
    #print(all_author_line)
    pdf_author_block=[]
    inst_tag=set(',')
    
    
    sign=False
    author_count=0
    for i in range(len(all_author_line)):
        #首先将每个作者行，分解为单个作者
        temp_list=[]
        block_author_list=re.split(r'[,]| and |and ',all_author_line[i])
        for each_author in block_author_list:
            each_author=each_author.strip()
            sign=False
            #如果只有一个字符，则应该是分割出来的同一个作者隶属的的几个机构的tag之一，连接到对应作者上
            #在这里一般是前一个进入作者list的字符串
            if len(each_author) is 1:
                temp_list[-1]=temp_list[-1]+each_author
                inst_tag.add(each_author)
                continue
            #
            if each_author is not '':
                temp_list.append(each_author)
            
            #检查该作者是否在给出的作者列表中出现
            for i in range(len(author_list)):
                if author_list[i] in each_author:
                    sign=True
                    #如果出现过，则尝试读取是否有交叉引用的机构tag
                    if each_author[-1]!=author_list[i][-1]:
                        inst_tag=inst_tag|set(each_author.replace(author_list[i],''))
                    break
            #如果没有出现过，则读取最后一个字符视为机构tag，并在后续进行分辨
            if sign is not True and each_author is not '':
                inst_tag.add(each_author[-1])
                print("cant find author "+each_author)
        pdf_author_block.append(temp_list)

    #对从作者中读取出的机构tag进行清洗，去除明显不是tag的
    inst_tag=inst_tag-set(', abcdefghijklmnopqrstuvwxyz')
    
    #根据读取出的tag数目，作者行数，判断是否存在交叉引用，以及是否有注释
    cross_infer =False
    have_comment=False
    if(len(all_author_line) is 1) and (len(inst_tag)>1):
        cross_infer=True
        inst_tag=''.join(list(inst_tag))
    elif len(inst_tag) is 1:
        inst_tag=inst_tag[0]
        have_comment=True
    else:
        cross_infer=False

    #print(inst_tag)
    
    #print(all_inst_line)
    #用于去除邮箱大括号的正则表达式
    braces_detect=re.compile(r'{.+?}')
    #对所有机构行进行分割，按照邮箱，交叉引用tag，作者空行（原来的作者行被替换为空格）
    now_num=0
    all_inst_block=[]
    all_tag=[]
    temp_block=[]
    sign=False
    for el in all_inst_line:
        #有空行，则结束前一个机构块
        if el is '':
            if sign is True:
                all_inst_block.append(temp_block)
                sign=False
                now_num=now_num+1
                temp_block=[]
            continue
        #替换大括号，进一步分割每个机构行，将同一块中的机构转化为列表
        el=braces_detect.sub('',el)
        all_enti=re.split('[,]|Email',el)
        #print(all_enti)
        for each_e in all_enti:
            each_e=each_e.strip()
            if each_e is '' or ('@' in each_e):
                if sign is True:
                    all_inst_block.append(temp_block)
                    sign=False
                    now_num=now_num+1
                    temp_block=[]
            elif (cross_infer or have_comment) and each_e[0] in inst_tag:
                if sign is True:
                    all_inst_block.append(temp_block)
                    now_num=now_num+1
                    temp_block=[]
                sign=True
                temp_block.append(each_e[1:].strip())
                all_tag.append(each_e[0])
            else: 
                sign=True
                if have_comment and each_e[0] is inst_tag:
                    each_e=each_e[1:]
                temp_block.append(each_e)
                
    if len(temp_block)>0:
        all_inst_block.append(temp_block)

     
    #print(pdf_author_block)
    #print(all_inst_block)
    #print("all_tag is ",end='')
    #print(all_tag)


    #得到用于替换的正则表达式,得到去除tag后的作者列表
    inst_tag=set(inst_tag)|set(all_tag)
    inst_tag=''.join(inst_tag)
    tag_detect=re.compile('['+inst_tag+']')
    clear_all_author=[]
    for i in range(len(pdf_author_block)):
        for j in pdf_author_block[i]:
            if have_comment or cross_infer:
                j=tag_detect.sub('',j)
            clear_all_author.append(j)
    
    #根据之前的信息，输出作者列表，机构列表，对应关系列表
    author_inst_infer_list=[]
    temp_infer_list=[]
    
    match_sign=False
    if cross_infer:
        match_sign=True
        all_author=pdf_author_block[0]
        for ea in all_author:
            temp_infer_list=[]
            for i in range(len(all_tag)):
                if all_tag[i] in ea:
                    temp_infer_list.append(i)
            author_inst_infer_list.append(temp_infer_list)
    else:
        if len(all_inst_block)!=len(pdf_author_block):
            match_sign=False
            print("cant read out!")
            return [pdf_title,clear_all_author,all_inst_block,match_sign]
        
        match_sign=True
        link_inst_block=[]
        temp_inst_block=[]
        temp_inst=''
        repeat_sign=False
        repeat_num=0
        infer_num=0
        for i in range(len(pdf_author_block)):
            repeat_sign=False
            temp_inst=','.join(all_inst_block[i])
            for j in range(len(link_inst_block)):
                if temp_inst == link_inst_block[j]:
                    repeat_sign=True
                    repeat_num=j
                    break
            if repeat_sign:
                infer_num=j
            else:
                infer_num=len(link_inst_block)
                link_inst_block.append(temp_inst)
                temp_inst_block.append(all_inst_block[i])
            for j in range(len(pdf_author_block[i])):
                author_inst_infer_list.append([infer_num])
                
        all_inst_block=temp_inst_block
        
    return [pdf_title,clear_all_author,all_inst_block,match_sign,author_inst_infer_list]

class PDFReader:
    block_string=[['@@INFO@@'],['ABSTRACT','abstract','Abstract'],['KEYWORDS','keywords','Keywords'],
    ['INTRODUCTION','1 INTRODUCTION','Introduction','1 Introduction'],['CCS CONCEPTS']]
    def __init__(self,read_file,start_page=0,end_page=1,save_file='',max_part_num=1):

        self.read_file=read_file
        self.save_file=save_file
        self.sfp=None
        self.rfp=None

        self.now_para=''
        self.now_part=''
        self.now_part_kind=0
        self.all_part=[]
        self.all_part_kind=[]
        self.part_count=0
        self.max_part_num=max_part_num
        self.read_end=False

        self.start_page=start_page
        self.end_page=end_page
        self.now_page_num=0

        self.pre_para_end=0
        return 
    def startread(self,start_page=0,end_page=1,max_part_num=1):
        self.max_part_num=max_part_num
        self.end_page=end_page
        self.read_end=False
        self.start_page=start_page
        #print(self.read_file)

        try:
            if self.read_file.startswith('http'):
                headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
                req = Request(url=self.read_file, headers=headers)
                file_string=urlopen(req).read()
                all_content=BytesIO(file_string)
            else:
                all_content=open(self.read_file,'rb')
        except Exception as e:
            print('Error:',e)
            return False
            
        #来创建一个pdf文档分析器
        parser = PDFParser(all_content)
        #创建一个PDF文档对象存储文档结构
        document = PDFDocument(parser)
        # 检查文件是否允许文本提取
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        else:
            # 创建一个PDF资源管理器对象来存储共赏资源
            rsrcmgr=PDFResourceManager()
            # 设定参数进行分析
            laparams=LAParams()
            # 创建一个PDF设备对象
            device=PDFPageAggregator(rsrcmgr,laparams=laparams)
            # 创建一个PDF解释器对象
            interpreter=PDFPageInterpreter(rsrcmgr,device)
            # 只需要处理第一页
            all_pages=PDFPage.create_pages(document)
            #first_page =all_pages.__next__()
            #second_page=all_pages.__next__()
            now_page_num=0
            for page in all_pages:
                print(now_page_num)
                if now_page_num<self.start_page:
                    now_page_num=now_page_num+1
                    continue
                interpreter.process_page(page)
                    # 接受该页面的LTPage对象
                layout=device.get_result()
                self.dyextractLT(layout)
                self.pre_para_end=0
                if self.read_end or now_page_num>=self.end_page:
                    self.savepart()
                    break
                now_page_num+=1
        all_content.close()
        return True
    def savepara(self):
        s_rep1=re.compile(r'\s+')
        s_rep2=re.compile(r' +')
        block_rep=''
        temp_para=self.now_para.strip()
        self.now_para=''
        if temp_para=='':
            return 
        base_kind=0
        find_sign=False
        for ekp in self.block_string:
            find_sign=False
            for ekpk in ekp:
                if temp_para.startswith(ekpk):
                    find_sign=True
                    block_rep=r'\A'
                    block_rep+=ekpk+'[^A-Z]*'
                    block_rep=re.compile(block_rep)
                    temp_para=block_rep.sub('',temp_para).strip()
                    break
            if find_sign:
                break
            base_kind+=1
        
        if self.now_part_kind!=0 or find_sign:
            temp_para=s_rep1.sub(' ',temp_para)
        if find_sign:
            self.all_part.append(self.now_part)
            self.all_part_kind.append(self.now_part_kind)
            self.now_part=temp_para+'\n'
            self.now_part_kind=base_kind
            self.part_count+=1
        else:
            self.now_part+=temp_para+'\n'
        if self.part_count>=self.max_part_num:
            self.read_end=True
        
        return
    def savepart(self):
        if self.now_part=='':
            return
        self.all_part.append(self.now_part)
        self.all_part_kind.append(self.now_part_kind)
        self.now_part=''
        self.now_part_kind=-1
        return
    def dyextractLT(self,each_ltobj):
        pre_wid=0
        pre_hei=0
        up_pos=0
        down_pos=0
        pre_end=0
        
        for x in each_ltobj:
            #遍历所有子对象，处理
            #print(x.__class__.__name__)
            now_bbox=x.bbox
            #print(now_bbox)
            if isinstance(x,LTChar) or isinstance(x,LTTextLine):
                x_str=x.get_text()
                char_count=len(x_str)
                this_wid=now_bbox[2]-now_bbox[0]
                this_hei=now_bbox[1]-now_bbox[3]
                c_wid=this_wid/char_count
                if up_pos>now_bbox[3] or down_pos<now_bbox[1]:
                    if up_pos!=now_bbox[1] or down_pos!=now_bbox[3] or pre_end<now_bbox[0]:
                        self.now_para=self.now_para+' '
                else:
                    if this_hei!=pre_hei or pre_end<(self.pre_para_end-5*c_wid) or self.now_part_kind==0:
                        #print(self.now_para)
                        self.savepara()
                self.now_para=self.now_para+x_str
                
                if pre_end >self.pre_para_end:
                    self.pre_para_end=pre_end
                up_pos=now_bbox[1]
                down_pos=now_bbox[3]
                pre_hei=this_hei
                pre_end=now_bbox[2]
            else:
                self.savepara()
                if  isinstance(x,LTTextBox) or isinstance(x,LTTextBoxHorizontal):
                    self.now_para=x.get_text()
                    #print(self.now_para)
                    self.savepara()
                elif isinstance(x,LTFigure):
                    self.dyextractLT(x)
            if self.read_end:
                break
        if self.now_para is not '':
            self.savepara()
        return
    def saveinfile(self,save_file=''):
        self.save_file=save_file
        if self.save_file=='':
            return
        try:
            save_fp=open(self.save_file,'w',encoding='utf-8')
        except Exception as e:
            print(e)
            print('save_file error\n')
            return
        for i in range(len(self.all_part)):
            save_fp.write(self.block_string[self.all_part_kind[i]][0]+'\n')
            save_fp.write(self.all_part[i])
        save_fp.close()
        return
    def getabs(self):
        pdf_abs=''
        for i in range(len(self.all_part)):
            if self.all_part_kind[i]==1:
                pdf_abs=self.all_part[i]
        return pdf_abs
    def printout(self):
        for i in range(len(self.all_part)):
            print(self.block_string[self.all_part_kind[i]][0])
            print(self.all_part[i])
        return

if __name__ == '__main__':
    #usenix示例，因为第一页是usenix封面，所以从1开始读

    testlink1='D:/课程/secconfdata/sec18-scaife.pdf'
    #网页也可以读,会比较慢
    #testlink1='https://www.usenix.org/system/files/conference/usenixsecurity18/sec18-scaife.pdf'
    test_reader1=PDFReader(testlink1)
    #1 是开始读的页数，2是结束的页数，2是读到摘要就停
    test_reader1.startread(1,2,2)
    abs_str=str(test_reader1.getabs())
    print(abs_str)
    #ndss ccs IEEE 示例
    '''
    testlink2='https://www.ndss-symposium.org/wp-content/uploads/2017/09/Document-Structure-Integrity-A-Robust-Basis-for-Cross-site-Scripting-Defense-Yacin-Nadji.pdf'
    test_reader2=PDFReader(testlink1)
    test_reader2.startread(0,1,2)
    abs_str=str(test_reader2.getabs())
    print(abs_str)
    '''



#   作者信息有可能在备注里，作者名会带*十字等奇怪符号，邮箱字符串处理，部门包含学校与学院，国家，城市，且与邮箱的位置不固定

# 会议信息单独列数据库存储，机构与国家对应信息单独列数据库处理，作者信息单独列数据库处理，包含年份，部门，机构，地区，国家，邮箱


# 有可能同一个机构的作者块中，不是由同一行构成，故在读取作者块时做拼接处理


# QQQQQQ可能使用交叉引用来注明作者机构对应关系，使用一些特殊符号作为tag，放在作者名后，每个机构之前，比如*123$等，这种情况下，一般作者都放在一行（或作者太多，放在连续的几行）
# AAAAAA可以使用预先读取的作者信息，比对从pdf中读取的作者信息，如果有额外的非字母字符，且作者只有一行，应该是存在交叉引用




# 当使用tag进行对应时，可能不同的机构放在同一行，这时候要使用tag分割出来不同的机构块

#QQQQQQQ 对于tag，可能现有的编码无法显示，表示为（cid:数字）的形式，考虑解决
#AAAAAAA 使用正则表达式读取所有cid，替换为0到9的数字


#QQQQQQQ 有些文章中，将tag放在作者名前，考虑处理

#QQQQQQQ

#QQQQQQ 如果没有使用逗号分割同一行的所有不同机构，但有交叉应用tag，则如何保留Tag,并分割不同机构呢？
#例子：https://www.ndss-symposium.org/wp-content/uploads/2017/09/ads-safe-detecting-hidden-attacks-through-mobile-app-web-interfaces.pdf


#QQQQQ 如果作者使用了** 和*同时作为两个机构的tag，则如何分辨？
#例子：https://www.ndss-symposium.org/wp-content/uploads/2017/09/forwarding-loop-attacks-content-delivery-networks.pdf

#QQQQQQ 同一个作者的多个tag之间，可能使用逗号分割，而分割作者时，也使用逗号分割
#例子：https://www.usenix.org/conference/usenixsecurity19/presentation/cao
#AAAAAA 在使用逗号分割后，判断是否存在单字符，若存在，则视为tag连接到前一个作者上

#QQQQQ USENIXsecuirty 上的论文可能只有官方格式，作者信息在第二页

#QQQQQQQ

#QQQQQQ 处理作者的名称时，因为要以pdf为准，如果pdf中有注释，则读取出来的作者名会有误，导致最后写入数据库的名字有误

#QQQQQQQ  可能有作者不使用逗号分割自己的名字，以及

#QQQQQQQ 有的作者邮箱和机构连在一起，
#https://www.ndss-symposium.org/ndss2017/ndss-2017-programme/
#tumblebit-untrusted-bitcoin-compatible-anonymous-payment-hub/
#AAAAAA  替换大括号时替换为






















