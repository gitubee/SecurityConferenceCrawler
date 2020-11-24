import xlrd
import re
import pymysql


usenix = xlrd.open_workbook('D:/master/usenix2.xlsx')
u_sheet=usenix.sheets()[0]
col_num=u_sheet.nrows
conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
if __name__=='__main__':
    cursor1=conn.cursor()
    for i in range(col_num):
        this_row=u_sheet.row_values(i)
        print(this_row)
        this_line=['USENIX Security']+[int(this_row[1]),int(this_row[2])]+list(this_row)[3:]
        insert_sql='insert into all_article_usenix() values(%s,%s,%s,%s,%s,%s,%s)'
        cursor1.execute(insert_sql,this_line)
        conn.commit()
cursor1.close()
conn.close()
