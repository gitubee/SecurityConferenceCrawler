import requests
import re

import pymysql
from lxml import etree
import string

conn = pymysql.connect('localhost', user='root',password='123456',database='secconf',charset='utf8mb4')
cursor = conn.cursor()


