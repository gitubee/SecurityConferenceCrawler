import re


def removeblock(all_entity):
    s_rep=re.compile(r'\s+')
    out=[]
    for ei in all_entity:
        ei=s_rep.sub(' ',ei).strip()
        if ei!='':
            out.append(ei)
    return out
def compressinst(all_inst):
    if isinstance(all_inst,str):
        all_inst=re.split(r'[;]',all_inst)
    if not isinstance(all_inst,list):
        print('all_instance type error')
        return
    s_rep=re.compile(r'\s+')
    all_comp_inst=[]
    cross_infer=[]
    temp_infer=[]
    find_sign=False
    find_num=-1
    for eis in all_inst:
        eis=s_rep.sub(' ',eis)
        eis=re.split(r'[:;]',eis)
        temp_infer=[]
        for ei in eis:
            ei=ei.strip()
            find_sign=False
            for j in range(len(all_comp_inst)):
                if ei == all_comp_inst[j]:
                    find_sign=True
                    find_num=j
                    break
            if find_sign:
                temp_infer.append(find_num)
            else:
                temp_infer.append(len(all_comp_inst))
                all_comp_inst.append(ei)
        cross_infer.append(temp_infer)
    return cross_infer,all_comp_inst
def concateinfer(cross_infer):
    cross_infer_str=[]
    for eci in cross_infer:
        cross_infer_str.append(':'.join(list(map(str,eci))))
    return ';'.join(cross_infer_str)
def readcrossinfer(cross_infer_str):
    each_infer=re.split(';',cross_infer_str)
    out=[]
    temp=[]
    for ei in each_infer:
        temp=re.split(':',ei)
        temp=list(map(int,temp))
        out.append(temp)
    return out
def refreshindex(o_index,i_index):
    new_index=[]
    for eoi in o_index:
        ti=set()
        for eoii in eoi:
            ti=ti|set(i_index[eoii])
        ti=list(ti)
        new_index.append(ti)
    return new_index


def delsession(session_title,start_num=4,end_num=2):
    none_str='Potpourri'
    if none_str in session_title:
        return ''
    s_rep=re.compile(r'\s+')
    session_title=s_rep.sub(' ',session_title)
    session_title=session_title.strip()
    if session_title=='':
        return ''
    start_rep1=re.compile(r'^Session[0-9A-Za-z\-\s]*?:')
    
    start_rep2=re.compile(r'^[1-9A-Za-z\-#\s]*?:')
    start_rep3=re.compile(r'^Paper Session[0-9A-Za-z-\s]*?:')
    start_rep4=re.compile(r'^Session[0-9A-Za-z\-\s]*?\-\-')
    start_rep5=re.compile(r'^Session[0-9A-Za-z\-\s]*?\-')
    start_rep=[start_rep1,start_rep2,start_rep3,start_rep4,start_rep5]
    end_rep1=re.compile(r'[IV0-9]+$')
    end_rep2=re.compile(r'\([0-9]+\)$')
    end_rep=[end_rep1,end_rep2]
    
    for i in range(start_num):
        session_title=start_rep[i].sub('',session_title)
    for i in range(end_num):
        session_title=end_rep[i].sub('',session_title)

    session_title=session_title.strip()
    return session_title