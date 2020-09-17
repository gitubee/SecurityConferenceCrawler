import re
import pymysql

conn = pymysql.connect('localhost', user='root',password='root',database='pylink1',charset='utf8')
#cursor = conn.cursor()

conf_dict={'crypto':0,'asiacrypto':1,'eucrypto':2,'ieee S&P':3,'ndss':4,'USENIX Security':5,'ccs':6} 

def removeblock(author_list):
    global special_pattern
    re_info=re.compile(r'\s+')
    new_list=[]
    for es in author_list:
        temp=re_info.sub(' ',es).strip()
        if temp!='':
            new_list.append(temp)
    return new_list
def delsession(session_title):
    none_str='Potpourri'
    if none_str in session_title:
        return ''
    s_rep=re.compile(r'\s+')
    session_title=s_rep.sub(' ',session_title)
    session_title=session_title.strip()

    start_rep1=re.compile(r'^Session[0-9A-Za-z-\s]*?:')
    start_rep2=re.compile(r'^[1-9A-Za-z-\s]*?:')
    start_rep3=re.compile(r'^Paper Session[0-9A-Za-z-\s]*?:')
    start_rep4=re.compile(r'^Session[0-9A-Za-z-\s]*?--')

    end_rep1=re.compile(r'[IV0-9]+$')
    end_rep2=re.compile(r'([0-9]+)$')
    
    session_title=start_rep1.sub('',session_title)
    session_title=start_rep3.sub('',session_title)
    session_title=start_rep4.sub('',session_title)

    session_title=end_rep1.sub('',session_title)
    session_title=end_rep2.sub('',session_title)

    session_title=session_title.strip()
    return session_title


def preinsert(city_table,country_table):
    all_state_US=['AL', 'AK', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA',
             'MA', 'ME', 'MD', 'MI', 'MN', 'MO', 'MS', 'MT', 'NE', 'NC', 'ND', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK',
             'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'DC', 'WV', 'WI', 'WY']
    all_country=[['USA','America','U.S.','United States','United States of America'],
                 ['Canada'],['Mexico'],['Cuba'],['Ecuador'],['Uruguay'],
                 ['Brazil'],['Venezuela'],['Argentina'],['Chile'],
                 ['China','RPC'],['Hong Kong'],['Taiwan'],
                 ['Japan'],
                 ['South Korea','Korea'],
                 ['Singapore'],
                 ['Vietnam'],['Thailand'],['Philippines'],['Iran'],['Turkey'],['Israel'],
                 ['Uae'],['Yemen'],['Qatar'],['Pakistan'],
                 ['UK','United Kingdom','Britain','GRB','Great Britain','U.K.'],
                 ['Russia'],['France'],['Germany'],['Italy'],['Spain'],
                 ['Portugal'],['Ireland'],['Finland'],['Sweden'],['Norway'],['Denmark'],
                 ['Czech'],['Repslovakia'],['Belgium'],['the Netherlands','Holland'],
                 ['Hungary'],['Austria'],['Greece'],['Poland'],['Switzerland'],['Ukraine'],
                 ['Estonia'],['Iceland'],
                 ['Australia'],
                 ['South Africa']
                ]
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()

    city_insert_sql='insert into {}(city,country)values(%s,%s)'.format(city_table)
    country_insert_sql='insert into {}(country_name,common_name)values(%s,%s)'.format(country_table)
    for i in all_state_US:
        cursor1.execute(city_insert_sql,(i,'USA'))
    conn.commit()

    for each_n in all_country:
        this_name=each_n[0]
        for i in each_n:
            cursor2.execute(country_insert_sql,(i,this_name))
    conn.commit()
    return

def extractentity(from_table,f_column_name,to_table,t_column_name):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()

    select_sql='select {} from {}'.format(f_column_name,from_table)
    insert_sql='insert into {}({})values(%s)'.format(to_table,t_column_name)

    for year in range(2005,2021):
        where_sql=" where year='{}'".format(str(year))
        print(where_sql)
        cursor1.execute(select_sql+where_sql)
        for each_line in cursor1.fetchall():
            all_en=each_line[0]
            if all_en=='':
                continue
            all_en=re.split('[;]',all_en)
            for ee in all_en:
                find_sql='select * from {} where {}="{}"'.format(to_table,t_column_name,ee)
                cursor2.execute(find_sql)
                find_out=cursor2.fetchone()
                if find_out==None:
                    cursor2.execute(insert_sql,ee)
            conn.commit()
    
    return



def extract_article(article_table,out_table):
    global conn

    cursor1=conn.cursor()
    cursor2=conn.cursor()

    select_sql='select conf_name,year,number,title,all_author,session_title,keywords from {}'.format(article_table)
    article_insert_sql='insert into {}(conf_name,year,number,title,all_author,session_title,keywords)\
        values(%s,%s,%s,%s,%s,%s,%s)'.format(out_table)
    
    for year in range(2005,2021):
        where_sql=" where year='{}'".format(str(year))
        print(where_sql)
        cursor1.execute(select_sql+where_sql)
        for each_line in cursor1.fetchall():
            
            this_authors=each_line[4]
            if this_authors==None:
                this_authors=''
            else:
                this_authors=re.split(r'[,;]',this_authors)
                this_authors=removeblock(this_authors)
                this_authors=';'.join(this_authors)

            this_keywords=each_line[6]
            if this_keywords==None:
                this_keywords=''
            else:
                this_keywords=re.split(r'[;]',this_keywords)
                this_keywords=removeblock(this_keywords)
                this_keywords=';'.join(this_keywords)

            session=each_line[5]
            if session==None:
                session=''
            else:
                session=delsession(session)

            cursor2.execute(article_insert_sql,(each_line[0],each_line[1],each_line[2],each_line[3],this_authors,session,this_keywords))
            conn.commit()

    return




 
def judgecci(inst_info,inst_table,city_table):
    global conn

    cursor1=conn.cursor()
    cursor2=conn.cursor()
    
    all_part=re.split(r'[,;]',inst_info)
    this_country=''
    this_inst=all_part[0]
    pre_ep=''
    inst_find_sql='select country from {} where inst="{}"'.format(inst_table,inst_info)
    cursor1.execute(inst_find_sql)
    find_out=cursor1.fetchone()
    if find_out!=None:
        this_inst=inst_info
        this_country=find_out[0]
        return this_inst,this_country
    
    for ep in all_part:
        ep=ep.strip()
        this_p=ep.replace('Univ.','University')
        in_inst=False
        if ep=='Inc.':
            this_p=pre_ep+' '+ep
        inst_find_sql='select country from {} where inst="{}"'.format(inst_table,this_p)
        cursor1.execute(inst_find_sql)
        find_out=cursor1.fetchone()
        if find_out!=None:
            if find_out[0]!='' and ';' not in find_out[0]:
                this_country=find_out[0]
            
            if ep=='Inc.':
                this_inst=this_p
            elif ep not in this_inst:
                this_inst=this_inst+','+ep
            
            continue
        city_find_sql='select country from {} where city="{}"'.format(city_table,ep)
        #print(city_find_sql)
        cursor2.execute(city_find_sql)
        find_out=cursor2.fetchone()
        if find_out!=None:
            #print('find out city')
            this_country=find_out[0]
            break
    this_inst=inst_info
    inst_find_sql='select country from {} where inst="{}"'.format(inst_table,this_inst)
    cursor1.execute(inst_find_sql)
    find_out=cursor1.fetchone()
    if find_out==None:
        print(this_inst+' # '+this_country)
        insert_sql='insert into {}(inst,country)values(%s,%s)'.format(inst_table)
        cursor1.execute(insert_sql,(this_inst,this_country))
        conn.commit()
    elif find_out[0]!='' and ';' not in find_out[0] and this_country=='':
        this_country=find_out[0]
    
    return this_inst,this_country

def extractacci_ccs(article_table,author_table,inst_table,city_table,inst_info_col):
    global conn

    cursor1=conn.cursor()
    cursor2=conn.cursor()
    cursor3=conn.cursor()

    sel_sql='select conf_name,year,number,all_author,{} from {}'.format(inst_info_col,article_table)
    author_insert_sql='insert into {}(name,year,article_tag,author_order,inst,country)values(%s,%s,%s,%s,%s,%s)'.format(author_table)
    
    del_info=[]
    for year in range(2005,2021,1):
        where_sql=" where year={}".format(year)
        print(where_sql)
        cursor1.execute(sel_sql+where_sql)
        for each_line in cursor1.fetchall():
            del_info=[]
            all_author=re.split('[;]',each_line[-2])
            
            if each_line[-1]==None or each_line[-1]=='':
                all_inst_info=['' for x in range(len(all_author))]
            else:
                all_inst_info=re.split('[;]',each_line[-1])
            
            this_article_tag=each_line[0]+'-'+str(each_line[1])+'-'+str(each_line[2])
            if len(all_inst_info)!=len(all_author):
                print("@@@@@@@@@X@@@@@@@@")
                print(this_article_tag)
                continue
            au_order=0
            for i in range(len(all_inst_info)):
                
                if all_inst_info[i]=='':
                    continue
                have_sign=False
                for epd in del_info:
                    if all_inst_info[i]==epd[0]:
                        this_inst=epd[1]
                        this_country=epd[2]
                        have_sign=True
                        break
                if not have_sign:
                    this_inst,this_country=judgecci(all_inst_info[i],inst_table,city_table)
                    del_info.append([all_inst_info[i],this_inst,this_country])
                #print(all_inst_info[i]+' @ '+this_inst+' @ '+this_country)
                cursor2.execute(author_insert_sql,(all_author[i],str(each_line[1]),this_article_tag,au_order,this_inst,this_country))
                au_order=au_order+1
            conn.commit()        
    return
    
def getcountry_springer(inst,country):
    global conn
    cursor1=conn.cursor()
    #cursor2=conn.cursor()
    cursor3=conn.cursor()
    s_rep=re.compile(r'\s+')
    if inst=='':
        return ''
    inst=s_rep.sub(' ',inst).strip()
    all_inst=re.split(':',inst)
    out_country=['' for x in range(len(all_inst))]
    
    for i in range(len(all_inst)):
        if all_inst[i]=='':
            continue
        inst_sql="select country from institution where inst='{}'".format(all_inst[i])
        cursor1.execute(inst_sql)
        find_out=cursor1.fetchone()
        if find_out==None:
            continue
        elif ':' in find_out[0] or find_out[0]=='':
            continue
        out_country[i]=find_out[0]
    
    if country!='':
        country=s_rep.sub(' ',country).strip()
        all_country=re.split(':',country)
        for i in range(len(all_country)):
            if all_country[i]=='':
                continue
            country_sql="select common_name from country where country_name='{}'".format(all_country[i])
            cursor3.execute(country_sql)
            find_out=cursor3.fetchone()
            if find_out==None:
                continue
            elif ':' in find_out[0] or find_out[0]=='':
                continue
            out_country[i]=find_out[0]
    cursor1.close()
    #cursor2.close()
    cursor3.close()
    return out_country
    
def extractauthor_springer(article_table,author_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    

    s_rep=re.compile(r'\s+')
    article_sel_sql1='select conf_name,number,title,all_author,all_inst,all_country from {} '.format(article_table)
    for year in range(2005,2020):
        where_sql2=' where year={};'.format(year)
        cursor1.execute(article_sel_sql1+where_sql2)
        
        insert_sql='insert into {}(name,year,article_tag,author_order,title,inst,country)values(%s,%s,%s,%s,%s,%s,%s)'.format(author_table)
        print(insert_sql)
        for each_line in cursor1.fetchall():
            article_tag=['','','']
            article_tag[0]=each_line[0]
            article_tag[1]=str(year)
            article_tag[2]=str(each_line[1])
            article_tag='-'.join(article_tag)
            title=each_line[2]
            all_author=re.split(';',each_line[3])
            all_inst=re.split(';',each_line[4])
            all_country=re.split(';',each_line[5])
            
            if len(all_inst)==0 or (len(all_inst)==1 and all_inst[0]==''):
                all_inst=['' for i in range(len(all_author))]
                
                all_country=['' for i in range(len(all_author))]
            else:
                if len(all_country)==0 or (len(all_country)==1 and all_country[0]==''):
                    all_country=['' for i in range(len(all_author))]
            #print(all_author)
            #print(all_inst)
            #print(all_country)
            for i in range(len(all_author)):

                have_city=False
                this_country=getcountry_springer(all_inst[i],all_country[i])
                this_country=':'.join(this_country)
                
                #print(article_tag)
                #print(this_country)
                
                cursor2.execute(insert_sql,(all_author[i],year,article_tag,i,title,all_inst[i],this_country))
        conn.commit()
            #print(i)
            #continue
    cursor1.close()
    cursor2.close()
    return
def extractinst(article_table,inst_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    cursor3=conn.cursor()

    s_rep=re.compile(r'\s+')
    sql1='select all_inst,all_country from {}'.format(article_table)
    insert_sql1='insert into {}(inst,country)values(%s,%s)'.format(inst_table)
    country_find_sql='selec'

    for year in range(2005,2020):
        where_sql=' where year={}'.format(year)
        cursor1.execute(sql1+where_sql)
        for each_line in cursor1.fetchall():
            print(each_line[0])
            print(each_line[1])
            all_inst=re.split(r'[:;]',each_line[0])
            all_country=re.split(r'[:;]',each_line[1])
            #print(all_inst)
            #print(all_country)
            if len(all_inst)==0 or (len(all_inst)==1 and all_inst[0]==''):
                continue
            if len(all_country)==0 or (len(all_country)==1 and all_country[0]==''):
                all_country=['' for i in range(len(all_inst))]
            elif len(all_inst)!=len(all_country):
                print(each_line[0])
                print(each_line[1])
            for i in range(len(all_inst)):
                this_inst=s_rep.sub(' ',all_inst[i]).strip()
                this_country=s_rep.sub(' ',all_country[i]).strip()
                if this_inst=='':
                    continue
                #print(this_inst)
                #print(this_country)
                country_find_sql="select common_name from country where country_name='{}'".format(this_country)
                cursor3.execute(country_find_sql)
                find_out=cursor3.fetchone()
                this_country=find_out[0]
                
                find_sql="select country from {} where inst='{}'".format(inst_table,this_inst)
                cursor2.execute(find_sql)
                find_out=cursor2.fetchone()
                if find_out==None:
                    cursor2.execute(insert_sql1,(this_inst,this_country))
                elif this_country not in find_out[0]:
                    country_str=find_out[0]+';'+this_country
                    modify_sql="update {} set country='{}' where inst='{}'".format(inst_table,country_str,this_inst)
                    cursor2.execute(modify_sql)
            conn.commit()
                
    cursor1.close()
    cursor2.close()
    return
def shifttocity(city_table,country_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    sel_sql='select * from {}'.format(country_table)
    insert_sql='insert into {}(city,country)values(%s,%s)'.format(city_table)
    cursor1.execute(sel_sql)

    for each_line in cursor1.fetchall():
        find_sql="select * from {} where city='{}'".format(city_table,each_line[0])
        #print(each_line)
        cursor2.execute(find_sql)
        find_out=cursor2.fetchone()
        #print(find_out)
        if find_out ==None:
            cursor2.execute(insert_sql,each_line)
        conn.commit()
    return
def removerepeat(entity_table,country_table,entity_column):
    global conn

    cursor1=conn.cursor()
    cursor2=conn.cursor()
    cursor3=conn.cursor()

    
    sql1='select * from {}'.format(entity_table)
    cursor1.execute(sql1)
    #首先，根据更新后的国家表，将重复的国家信息去除
    for each_line in cursor1.fetchall():
        #print(each_line)
        entity_name=each_line[0]
        country_name=each_line[1].strip()
        if country_name=='':
            continue
        all_country=re.split('[:;]',country_name)
        country_str=''
        for ec in all_country:
            ec=ec.strip()
            if ec=='':
                continue
            #print(ec)
            find_sql1="select common_name from {} where country_name='{}'".format(country_table,ec)
            cursor3.execute(find_sql1)
            find_out=cursor3.fetchone()
            this_c=find_out[0]
            if this_c not in country_str:
                if country_str=='':
                    country_str=this_c
                else:
                    country_str=country_str+';'+this_c
        modify_sql="update {} set country='{}' where {}='{}'".format(entity_table,country_str,entity_column,entity_name)
        cursor2.execute(modify_sql)
        conn.commit()
    cursor1.close()
    cursor2.close()
    cursor3.close()
    return

'''
def locateinst(inst_table,country_table):
    global conn

    cursor1=conn.cursor()
    cursor2=conn.cursor()
    #cursor3=conn.cursor()
    sql1='select * from {}'.format(inst_table1)
    cursor1.execute(sql1)
    

    #对没有国家的机构进行处理，提取它的每一部分尝试匹配机构
    for each_line in cursor1.fetchall():
        inst_name=each_line[0]
        country_name=each_line[1]
        if country_name!='':
            continue
        all_inst_part=re.split('[:;]',country_name)
        country_str=''
        for ep in all_inst_part:
            ep=ep.strip()
            find_sql2="select country_name from {} where inst_name='{}'".format(inst_table,ep)
            cursor2.execute(find_sql2)
            find_out=cursor3.fetchone()
            country_str=''
            if find_out==None:
                continue
            this_c=find_out[0]
            all_c=re.split('[:;]',this_c)
            for ec in all_c:
                if ec not in country_str:
                    if country_str=='':
                        country_str=this_c
                    else:
                        country_str=countrt_str+';'+this_c
        modify_sql="update {} set country_name='{}' where inst_name='{}'".format(inst_table,inst_name,country_str)
        cursor2.execute(modify_sql)
        conn.commit()
    


    cursor1.close()
    cursor2.close()
    return 
'''

def correctauthor(author_table,inst_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    cursor3=conn.cursor()
    select_sql='select name,article_tag,inst,country from {}'.format(author_table)
    cursor1.execute(select_sql)
    for each_line in cursor1.fetchall():
        if ';' not in each_line[3]:
            continue
        print(each_line)
        all_inst=re.split(r'[:]',each_line[2])
        all_co=re.split(r'[:]',each_line[3])
        if len(all_inst)!=len(all_co):
            print(each_line)
            continue
        for i in range(len(all_inst)):
            if ';' not in all_co[i]:
                continue
            find_sql='select country from {} where inst="{}"'.format(inst_table,all_inst[i])
            cursor2.execute(find_sql)
            find_out=cursor2.fetchone()
            if find_out==None:
                print(find_sql)
                continue
            find_co=find_out[0]
            if ';' not in find_co:
                all_co[i]=find_co
            else:
                all_co[i]=''
        this_co=':'.join(all_co)
        print(each_line[3]+'#'+this_co)
        modify_sql='update {} set country="{}" where name="{}" and article_tag="{}"'.format(author_table,this_co,each_line[0],each_line[1])
        cursor3.execute(modify_sql)
        conn.commit()

    return

def countauthor(article_table):
    global conn
    cursor1=conn.cursor()
    author_dict={}
    select_sql='select all_author from {} where conf_name="crypto" or conf_name="aisacrypto" or conf_name="eurocrypto"'.format(article_table)
    art_c=0
    
    cursor1.execute(select_sql)
    for each_line in cursor1.fetchall():
        art_c=art_c+1
        each_line=each_line[0].strip()
        if each_line=='':
            continue
        all_author=re.split(r'[;]',each_line)
        for ea in all_author:
            if ea not in author_dict:
                author_dict[ea]=1
            else:
                author_dict[ea]=author_dict[ea]+1
    print(art_c)
    sort_dict=sorted(author_dict.items(),key = lambda kv:(kv[1], kv[0]),reverse=True)
    print(sort_dict[0:30])
    return

def countentity(author_table_list,sel_col):
    global conn
    cursor1=conn.cursor()
    entity_dict={}
    
    for each_table in author_table_list:
        select_sql="select {} from {}".format(sel_col,each_table)
        cursor1.execute(select_sql)
        for each_line in cursor1.fetchall():
            each_line=each_line[0].strip()
            if each_line=='':
                continue
            all_entity=re.split(r'[:;]',each_line)
            for ee in all_entity:
                if ee not in entity_dict:
                    entity_dict[ee]=1
                else:
                    entity_dict[ee]=entity_dict[ee]+1
    sort_dict=sorted(entity_dict.items(),key = lambda kv:(kv[1], kv[0]),reverse=True)
    print(sort_dict[0:30])
    return

def checkcity(city_table):
    global conn

    cursor=conn.cursor()
    select_sql='select * from {}'.format(city_table)
    cursor.execute(select_sql)
    for each_line in cursor.fetchall():
        print(each_line)
        if each_line[1]=='':
            print(each_line)
    cursor.close()
    return
def extractcitycountry_springer(article_table,city_table,country_table):
    global conn
    cursor1=conn.cursor()
    cursor2=conn.cursor()
    #cursor3=conn.cursor()
    cursor4=conn.cursor()
    s_rep=re.compile(r'\s+')
    sql1='select all_city,all_country from {} '.format(article_table)
    insert_sql1='insert into {}(city,country)values(%s,%s)'.format(city_table)
    #insert_sql2='insert into {}(city)values(%s)'.format(city_table)
    insert_sql3='insert into {}(country_name,common_name)values(%s,%s)'.format(country_table)
    
    for year in range(2005,2020):
        sql2="where year={};".format(year)
        cursor1.execute(sql1+sql2)
        
        #find_sql=''
        for each_line in cursor1.fetchall():
            #print(each_line)
            all_country=re.split(r'[:;]',each_line[1].strip())
            all_city=re.split(r'[:;]',each_line[0].strip())
            #print(all_country)
            #print(all_city)

            #首先利用读取出来的国家，得到国家列表，用于之后的手动校正
            for each_coun in all_country:
                this_country=s_rep.sub(' ',each_coun).strip()
                if this_country!='':
                    country_find_sql="select common_name from {} where country_name='{}'".format(country_table,this_country)
                    cursor4.execute(country_find_sql)
                    find_out=cursor4.fetchone()
                    if find_out ==None:
                        cursor4.execute(insert_sql3,(this_country,this_country))
                        conn.commit()
            
            #删去没有城市的信息，填入数据库中的国家城市表格
            if len(all_city)==0 or (len(all_city)==1 and all_city[0]==''):
                continue
            elif len(all_country)==0 or (len(all_country)==1 and all_country[0]==''):
                #print('country none')
                all_country=['' for x in range(len(all_city))]
                #print(all_country)
            elif len(all_country)!=len(all_city):
                print('error')
                print(each_line)
                print('###############')
                
            for i in range(len(all_city)):
                #print(i)
                this_city=s_rep.sub(' ',all_city[i]).strip()
                this_country=s_rep.sub(' ',all_country[i]).strip()
                if this_city=='':
                    continue
                #print(this_city+' '+this_country)
                #开始检索并插入城市国家列表，检索得到的结果决定是否更新和插入
                city_find_sql="select country from {} where city='{}'".format(city_table,this_city)
                cursor2.execute(city_find_sql)
                find_out=cursor2.fetchone()
                if find_out==None:
                    cursor2.execute(insert_sql1,(this_city,this_country))
                    conn.commit()
                elif this_country not in find_out[0]:
                    country_str=find_out[0]+';'+this_country
                    modify_sql="update {} set country='{}' where city='{}'".format(city_table,country_str,this_city)
                    cursor2.execute(modify_sql)
                    conn.commit()

    cursor1.close()
    cursor2.close()
    #cursor3.close()
    cursor4.close()
    return
#preinsert('city_country','country')
#checkcity('city_country')
#shifttocity('city_country','country')
#removerepeat('institution','country','inst')
#extractcitycountry_springer('springer_article_info','city_country','country')
#extractinst('springer_article_info_lessdata','institution')
#extractauthor_springer('springer_article_info_lessdata','all_author')
#print(conf_dict['ccs'])
#verify_inst_table('testtable','a')
#cursor=conn.cursor()
#sql='insert into city_country(city,country)values(%s,%s)'
#cursor.execute(sql,('torato','Canada'))
#cursor.close()

print('vscode')
#extractacci_ccs('pre_info','all_author_un','institution','city_country','all_inst')
#extract_article('ieeesp_article_info','all_article')
#extractentity('all_article','all_author','all_author_name','author_name')
#ieeesp 2019 81
#correctauthor('all_author_un','institution')
#countauthor('all_article')
countentity(['all_author_springer'],'inst')
#countentity(['all_author_ccs','all_author_ieee','all_author_un'],'inst')
conn.close()
