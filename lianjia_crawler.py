
# coding: utf-8

# In[ ]:


# Author Morning67373 xianbin.xie@tum.de
# Created on 26-09-2018
# Created by Python 3


import csv
import requests
import re
from bs4 import BeautifulSoup
import time
import pandas as pd


# 请在这里声明全局变量city_name，city_name为链家的城市缩写，例如上海为sh、南京为nj
city_name = 'sh'
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.92 Safari/537.36'}


def get_region_list(city_name):
    
    region_list = [] ### 储存每个城市下面有几个区域
    
    url = 'https://' + city_name + '.lianjia.com/xiaoqu/'
    res = requests.get(url, headers = headers)
    soup = BeautifulSoup(res.text, 'lxml')
    
    for a in soup.find_all('div', {'data-role': 'ershoufang'})[0].div.find_all('a'):
        region_list.append(a['href'])
    
    return region_list


def get_street_list(city_name, region_list):
    
    street_list = [] ###储存每个区域下面有几个街道
    
    for region in region_list:
        url = 'https://' + city_name + '.lianjia.com' + region
        print(url)
        res = requests.get(url, headers = headers)
        soup = BeautifulSoup(res.text, 'lxml')        
        for a in soup.find_all('div', {'data-role': 'ershoufang'})[0].find_all('div')[1].find_all('a'):
            street_list.append(a['href'])
        
    return street_list


def get_page(url):
    res = requests.get(url, headers = headers)
    soup = BeautifulSoup(res.text, 'lxml')
    page = int(re.sub("\D", "", soup.find_all(class_ = 'page-box house-lst-page-box')[0]['page-data'].split(',')[0])) ###每个街区下有几页
    return page


def get_district_list(url):
    
    district = [] ###存储每个街道下面的小区的url
            
    try:
        res = requests.get(url, headers = headers)
        soup = BeautifulSoup(res.text, 'lxml')
        for item in soup.find_all(class_ = 'clear xiaoquListItem'):
            district_list.append(item.find_all(class_ = 'title')[0].a['href'])   ### 每个小区的url
        return district

    except Exception as e:
        print(e)
        return []    


def remove_repeat(district_list):
    district_unique = []
    for item in district_list:
        if item not in district_unique:
            district_unique.append(item)
    return district_unique


def get_detail(url):
    info = {}
    
    try:
        res = requests.get(url, headers = headers)
        soup = BeautifulSoup(res.text, 'lxml')
        
        info['url'] = url
        info['geocode'] = soup.find_all('script', {'type': 'text/javascript'})[1].contents[0].split('\'')[3]
        info['name'] = soup.find_all(class_ = 'detailTitle')[0].contents[0] ### name
        info['address'] = soup.find_all(class_ = 'detailDesc')[0].contents[0]  ### address
        info['follow_number'] = soup.find_all('span', {'data-role': 'followNumber'})[0].contents[0]  ### follow_number
        
        if len(soup.find_all(class_ = 'xiaoquUnitPrice')) == 0:
            info['price'] = None
        else:
            info['price'] = soup.find_all(class_ = 'xiaoquUnitPrice')[0].contents[0]  ### price
        
        info['year'] = soup.find_all(class_ = 'xiaoquInfoContent')[0].contents[0]  ### year
        info['structure'] = soup.find_all(class_ = 'xiaoquInfoContent')[1].contents[0]  ### structure
        info['service_fee'] = soup.find_all(class_ = 'xiaoquInfoContent')[2].contents[0]  ### service_fee
        info['service_company'] = soup.find_all(class_ = 'xiaoquInfoContent')[3].contents[0]  ### service_company
        info['Immobilien'] = soup.find_all(class_ = 'xiaoquInfoContent')[4].contents[0]  ### Immobilien
        info['num_buildings'] = soup.find_all(class_ = 'xiaoquInfoContent')[5].contents[0]  ### num_buildings
        info['num_household'] = soup.find_all(class_ = 'xiaoquInfoContent')[6].contents[0]  ### num_household
        info['info_store'] = soup.find_all(class_ = 'xiaoquInfoContent')[7].contents[0]  ### info_store
        
        return info
    
    except Exception as e:
        print(e)
        return {} 

    
# 生成任务列表，所有需要爬取的小区的url会最终存储在一个csv里，等待后续爬取详细页面的时候调用
region_list = get_region_list(city_name = city_name)
street_list = get_street_list(city_name = city_name, region_list = region_list)

district_list = []
for street in street_list:
    url_street = 'https://' + city_name + '.lianjia.com' + street
    print(url_street)
    
    page = get_page(url = url_street)
    
    for i in range(page):
        url_page = url_street + 'pg' + str(i+1)  ### url of each page
        print(url_page)
        a = get_district_list(url = url_page)
        
        if len(a) == 0:
            time.sleep(5)
            a = get_district_list(url = url_page)  # 等待5秒后重新访问
            for item in a:
                district_list.append(item)
        else:
            for item in a:
                district_list.append(item)
                
# 任务列表里可能有重复的，下面去重
district_unique = remove_repeat(district_list = district_list)  
# 任务列表储存到csv
with open(city_name + 'district.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    for n in district_unique:
        writer.writerow([n])


# 访问每个url，获取详细页面的信息，这部分代码可以单独运行，但是必须导入好库和前面定义的函数
infos = []

with open(city_name + 'district.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        print(row[0])
        b = get_detail(url = row[0])
        if len(b) == 0:
            time.sleep(5)
            b = get_detail(url = row[0])  #等待5秒后重新访问
            infos.append(b)
        else:
            infos.append(b)


# 储存每个小区的信息，用csv储存可能出现encoding错误的问题，暂时不清楚原因，如果出错，请用下面注释掉的pandas的方法
headings = ['url', 'name', 'geocode', 'address', 'follow_number', 'price', 'year', 'structure', 'service_fee', 'service_company', 'Immobilien',
            'num_buildings', 'num_household', 'info_store']

with open(city_name + '.csv', 'a+', newline = '') as on:
    on_csv = csv.DictWriter(on, headings)
    on_csv.writeheader()
    on_csv.writerows(infos)

# tempdf = pd.DataFrame(infos)
# tempdf.to_csv(city_name + '.csv')

