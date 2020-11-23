import re
import pymysql
import string
import requests
from lxml import etree

conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')

equal_str={'Dept.':'Department','Univ.':'University','Res.':'Research','Corp.':'Corporation',
'Sci.':'Science','Coll.':'College','Inst.':'Institution','Inc.':'','Tech.':'Tech','Technol.':'Technology','Technologie':'Technology',
'Ltd.':'Limited','Calif.':'California','Département':'Department','Comp.':'Computer','Comput.':'Computer','Lab.':'Lab',
'Eng.':'Engineering','Inf.':'Information','Electr.':'Electr','Zürich':'Zurich','Zūrich':'Zurich',
'Bus.':'Business','Fac.':'Faculty','Eco.':'Economics'}
non_sence_str={'of','at','for','de','Für','The','the'}
def extractinfo(info_table,info_column,insert_table,insert_column):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    select_sql='select {} from {} '.format(info_column,info_table)
    insert_sql='insert into {}({}) values(%s)'.format(insert_table,insert_column)
    for i in range(2020,2021):
        where_sql='where year={}'.format(i)
        cursor1.execute(select_sql+where_sql)
        for el in cursor1.fetchall():
            all_inst_info=re.split(r';',el[0])
            for ei in all_inst_info:
                try:
                    cursor2.execute(insert_sql,ei)
                    print(ei)
                except:
                    a=1
            conn.commit()
    return

def geneproto(ori_str):
    and_rep=re.compile(r' and ')
    doge_rep=re.compile(r',')
    non_rep=re.compile(r'[/\-\s0-9\(\)&]+')
    #and_rep=re.compile(r' and ')
    yin_rep=re.compile(r"'|’|CEDEX|Cedex|cedex")
    proto_list=[]
    proto=ori_str
    proto=and_rep.sub(' & ',proto)
    proto=doge_rep.sub(' , ',proto)
    proto=yin_rep.sub('',proto)
    proto=non_rep.sub(' ',proto).strip()
    #print(proto)
    proto_list=[]
    modify_list=[]
    now_n=0
    pre_n=0
    for ec in proto:
        if ec==' ':
            if pre_n<now_n:
                proto_list.append(proto[pre_n:now_n])
            pre_n=now_n+1
        elif ec=='.':
            proto_list.append(proto[pre_n:now_n+1])
            pre_n=now_n+1
        elif ec.isupper():
            if pre_n<now_n:
                proto_list.append(proto[pre_n:now_n])
            pre_n=now_n
        now_n+=1
    if pre_n<now_n:
        proto_list.append(proto[pre_n:now_n])
    #print(proto_list)
    all_number=-1
    reflect_tag=[]
    for ew in proto_list:
        all_number+=1
        find_sign=False
        if ew=='&' or ew==',':
            continue
        for i in non_sence_str:
            if ew==i:
                find_sign=True
                break
        if find_sign:
            continue
        ew=ew.title()
        if ew in equal_str:
            ew=equal_str[ew]
        else:
            ew=ew.replace(".",'')
        if ew.startswith('Universi'):
            ew='University'
        proto_list[all_number]=ew
        modify_list.append(ew)
        reflect_tag.append(all_number)
    return modify_list,proto_list,reflect_tag

def genecityproto(city_table,proto_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    #cursor3=conn.cursor()
    select_sql='select * from {}'.format(city_table)
    insert_sql='insert into {}() values(%s,%s,%s,%s,%s)'.format(proto_table)
    cursor1.execute(select_sql)
    for el in cursor1.fetchall():
        city_proto_list=geneproto(el[0])
        country_proto_list=geneproto(el[1])
        city_proto=' '.join(city_proto_list)
        country_proto=' '.join(country_proto_list)
        try:
            cursor2.execute(insert_sql,(city_proto,country_proto,el[0],el[1],0))
        except :
            print(el)
    conn.commit()
    return

def trysplitproto(proto_list,search_table_list,block_search=True):
    global conn
    cursor1=conn.cursor()
    proto_block=[]
    block_tag=[]
    pos_tag=[]

    start_b=0
    end_b=len(proto_list)
    find_table_dict={}
    now_number=1
    now_block=''
    for i in range(start_b,end_b):
        if i<start_b:
            continue
        find_sign=False
        for j in range(end_b,start_b,-1):
            if find_sign:
                break
            if i==0 and j==end_b and not block_search:
                continue
            this_block=' '.join(proto_list[i:j])
            for each_table in search_table_list:
                select_sql="select proto from {} where proto='{}'".format(each_table,this_block)
                cursor1.execute(select_sql)
                getlie=cursor1.fetchall()
                if len(getlie)==0:
                    continue
                else:
                    if now_block!='':
                        proto_block.append(now_block)
                        block_tag.append(0)
                        pos_tag.append(i)
                        now_block=''
                    proto_block.append(this_block)
                    find_table_dict[now_number]=each_table
                    block_tag.append(now_number)
                    pos_tag.append(j)
                    now_number+=1
                    start_b=j
                    find_sign=True
                    break
        if find_sign:
            continue
        if now_block=='':
            now_block=proto_list[i]
        else:
            now_block+=' '+proto_list[i]
    if now_block!='':
        proto_block.append(now_block)
        block_tag.append(0)
        pos_tag.append(len(proto_list))

    #分块后的原型，每个原型块的标记，每个原型块在原型列表里的结束位置，每个原型块对应的表
    return proto_block,block_tag,pos_tag,find_table_dict

def delarealproto(proto_block,real_block,split_tag,tag_dict,belief=False):
    global conn
    cursor1=conn.cursor()
    select_sql=''
    this_country=''
    first_sign=False
    for i in range(len(proto_block)-1,-1,-1):
        if split_tag[i]==0:
            continue
        select_sql="select * from {} where proto='{}'".format(tag_dict[split_tag[i]],proto_block[i])
        cursor1.execute(select_sql)
        
    return

def generealentity(ori_list,ref_tag,pos_tag):
    entity_block=[]
    start_num=0
    for ep in pos_tag:
        this_pos=ref_tag[ep-1]+1
        now_block=''
        for j in range(start_num,this_pos):
            if (ori_list[j]=='&' or ori_list[j]==',') and now_block=='':
                continue
            if len(ori_list[j])==1 or now_block=='':
                now_block+=ori_list[j]
            else:
                now_block+=' '+ori_list[j]
        start_num=this_pos
        entity_block.append(now_block)
    return entity_block

def insertareainfo():
    global conn
    cursor1=conn.cursor()
    #cursor2=conn.cursor()
    select_sql='select citys,countrys from {} '.format('article_info_springer')
    for ey in range(1982,1983):
        now_num=0
        where_sql='where year={}'.format(str(ey))
        cursor1.execute(select_sql+where_sql)
        for el in cursor1.fetchall():
            all_city=re.split(r'[:;]',el[0])
            all_country=re.split(r'[;:]',el[1])
            if len(all_city)!=len(all_country):
                print('dont equal error'+el[0]+el[1])
                continue
            for i in range(len(all_city)):
                now_num+=1
                this_pair=all_city[i]+','+all_country[i]
                this_pair=this_pair.strip()
                if this_pair=='':
                    continue
                proto_list,ori_list,ref_tag=geneproto(this_pair)
                if len(proto_list)==0:
                    continue
                print(this_pair)
                proto_block,block_tag,pos_tag,tag_dict=trysplitproto(proto_list,['area_proto_info'])
                real_block=generealentity(ori_list,ref_tag,pos_tag)
                
                print(proto_block)
                print(ori_list)
                #print(block_tag)
                print(real_block)
                delarealproto(proto_block,real_block,block_tag,tag_dict,belief=True)
            
    return

            

def extractsubinfo(area_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    select_sql='select * from {}'.format(area_table)
    update_dql='update {} set sub_to={} where proto={} and sub_to={}'
    find_sql='select proto,country from {} where proto={} and {} in country'
    cursor1.execute(select_sql)
    for el in cursor1.fetchall():
        if el[-1]==1:
            continue
        proto_list=el[0].split()
        
        
    return

def findareaproto(area_table,country_table):
    return
def geneequal():
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    select_sql='select * from area_proto_info'
    cursor1.execute(select_sql)
    for el in cursor1.fetchall():
        #print(1)
        if el[5]=='1' and el[2]!=el[4]:
            update_sql="update area_proto_info set equal_to='{}' where proto='{}' and sub_to='{}'".format(el[4],el[0],el[1])
            cursor2.execute(update_sql)
            conn.commit()
            print(el)
    return


def testprotoblock(test_str):
    proto_list,ori_list,ref_tag=geneproto(test_str)         
    proto_block,block_tag,pos_tag,tag_dict=trysplitproto(proto_list,['area_proto_info'])
    real_block=generealentity(ori_list,ref_tag,pos_tag)
    print(proto_list)
    print(real_block)
    return


def judgecci(inst_info,inst_table,city_table):
    global conn
    
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    inst_info=inst_info.strip()
    all_part=re.split(r'[,;/\\:]',inst_info)
    this_country=''
    this_inst=all_part[0]
    pre_ep=''
    inst_find_sql='select country from {} where inst="{}"'.format(inst_table,inst_info)
    cursor1.execute(inst_find_sql)
    find_out=cursor1.fetchone()
    if find_out!=None:
        this_inst=inst_info
        if find_out[0]!='' and find_out[0]!=None and ';' not in find_out[0]:
            this_country=find_out[0]
            return this_inst,this_country
    
    for ep in all_part:
        ep=ep.strip()
        this_p=ep.replace('Univ.','University')
        if ep=='Inc.':
            this_p=pre_ep+' '+this_p
        pre_ep=ep
        inst_find_sql='select country from {} where inst="{}"'.format(inst_table,this_p)
        cursor1.execute(inst_find_sql)
        find_out=cursor1.fetchone()
        if find_out!=None:
            if ep=='Inc.':
                this_inst=this_p
            elif ep not in this_inst:
                this_inst=this_inst+','+ep
            if find_out[0]!='' and find_out[0]!=None and ';' not in find_out[0]:
                this_country=find_out[0]
                return this_inst,this_country
            continue
        city_find_sql='select country from {} where area="{}"'.format(city_table,ep)
        #print(city_find_sql)
        cursor2.execute(city_find_sql)
        find_out=cursor2.fetchone()
        if find_out!=None:
            #print('find out city')
            if ';' not in find_out[0]:
                this_country=find_out[0]
                break
    this_inst=inst_info
    
    print(this_inst+' # '+this_country)
    inst_find_sql='select country from {} where inst="{}"'.format(inst_table,this_inst)
    cursor1.execute(inst_find_sql)
    find_out=cursor1.fetchone()
    insert_sign=False
    modify_sign=False
    if find_out==None:
        insert_sign=True
        insert_coun=this_country
    elif find_out[0]==None or this_country not in find_out[0]:
        if find_out[0]==None or find_out[0]=='':
            insert_coun=this_country
        else:
            insert_coun=find_out[0]+';'+this_country
        modify_sign=True
    if insert_sign:
        insert_sql='insert into {}(inst,country)values(%s,%s)'.format(inst_table)
        cursor1.execute(insert_sql,(this_inst,insert_coun))
        conn.commit()
    if modify_sign:
        modify_sql='update {} set country="{}" where inst="{}"'.format(inst_table,this_country,this_inst)
        cursor1.execute(modify_sql)
        conn.commit()
    return this_inst,this_country

def extractacci_ccs(article_table,author_table,inst_table,city_table,inst_info_col):
    global conn

    cursor1=conn.cursor()
    cursor2=conn.cursor()
    cursor3=conn.cursor()

    sel_sql='select conf,year,authors,cross_infer,{},number from {}'.format(inst_info_col,article_table)
    author_insert_sql='insert into {}(name,year,article_tag,author_order,inst,country)values(%s,%s,%s,%s,%s,%s)'.format(author_table)
    
    del_info=[]
    for year in range(1980,2005,1):
        where_sql=" where year={}".format(year)
        print(where_sql)
        cursor1.execute(sel_sql+where_sql)
        number=-1
        for each_line in cursor1.fetchall():
            #number+=1
            #if (each_line[-1]-each_line[-2])<5:
                #continue
            number=each_line[-1]
            del_info=[]
            all_author=re.split('[;]',each_line[2])
            all_infer=re.split('[;]',each_line[3])
            all_inst_info=re.split('[;]',each_line[4])
            
            this_article_tag=each_line[0]+'-'+str(each_line[1])+'-'+str(number)
            if len(all_author)!=len(all_infer):
                print("@@@@@@@@@X@@@@@@@@")
                print(this_article_tag)
                continue
            for ei in all_inst_info:
                if ei=='':
                    del_info.append(['',''])
                    continue
                this_inst,this_country=judgecci(ei,inst_table,city_table)
                del_info.append([this_inst,this_country])
            for i in range(len(all_author)):
                if all_author[i]=='':
                    continue
                if ':' in all_infer[i]:
                    continue
                this_n=int(all_infer[i])
                if del_info[this_n][0]=='' and del_info[this_n][1]=='':
                    continue
                cursor2.execute(author_insert_sql,(all_author[i],each_line[1],this_article_tag,i,del_info[this_n][0],del_info[this_n][1]))
            conn.commit()        
    return
#insertareainfo()
#trysplitproto()
#geneequal()
#print(geneproto('Be’er Sheva'))
#print(geneproto('P.R. China'))
#genecountryproto('country','area_proto_info')
#genecityproto('ori_city_country','area_proto_info')
#print('a'.isupper())
#extractinfo('article_info_ccs','inst_info','inst_area_str','inst_area_str')
#extractacci_ccs('all_article_usenix','all_author_usenix','ori_inst','ori_city_country','inst_info')
conn.close()