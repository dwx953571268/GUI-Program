# -*- coding=utf-8 -*-
import requests,re,datetime
from  bs4 import BeautifulSoup
import sitecustomize
from requests.exceptions import Timeout,ConnectionError
import threading,os

class searcher:

    def __init__(self):
        self._hospital_dict={}
        self._consult_dict={}
        self._baseurl='http://www.bjguahao.gov.cn'
        self._search_result=[]
        self._appoint_url=""
        #多线程获取
        # self._lock=threading.Lock()
        # self._threads=[]

    # def get_hospital_multithread(self,i):
    #     url = 'http://www.bjguahao.gov.cn/hp/' + str(i) + ',0,0,0.htm?'
    #     try:
    #         wbtext=requests.get(url)
    #     except ConnectionError,e:
    #         raise e
    #     wbtext.encoding='utf-8'
    #     soup=BeautifulSoup(wbtext.text,'lxml',from_encoding='utf-8')
    #     for j in range(1,11):
    #         if i==16:
    #             if j==7:
    #                 return
    #         hospital = soup.select('#yiyuan_content > div:nth-of-type(' + str(j) + ') > dl > dd > p > a')[0].text
    #         hospital_url = soup.select('#yiyuan_content > div:nth-of-type(' + str(j) + ') > dl > dd > p > a')[0]['href']
    #         self._lock.acquire()
    #         try:
    #             self._hospital_dict[hospital] = self._baseurl + hospital_url
    #         finally:
    #             self._lock.release()
    #
    # def launch_multithread(self):
    #     for i in range(1, 17):
    #         self._threads.append(threading.Thread(target=self.get_hospital_multithread,args=(i,)))
    #     for t in self._threads:
    #         t.start()

    #从网络获取名单
    def get_hospital_from_net(self):
        hospital_file = open('hospital.txt', 'a+')
        for i in range(1, 17):
            url = 'http://www.bjguahao.gov.cn/hp/' + str(i) + ',0,0,0.htm?'
            try:
                wbtext = requests.get(url)
            except ConnectionError, e:
                raise e
            wbtext.encoding = 'utf-8'
            soup = BeautifulSoup(wbtext.text, 'lxml', from_encoding='utf-8')
            for j in range(1, 11):
                if i == 16:
                    if j == 7:
                        return
                hospital = soup.select('#yiyuan_content > div:nth-of-type(' + str(j) + ') > dl > dd > p > a')[0].text
                hospital_url = soup.select('#yiyuan_content > div:nth-of-type(' + str(j) + ') > dl > dd > p > a')[0][
                    'href']
                self._hospital_dict[hospital] = self._baseurl + hospital_url
                hospital_file.write(hospital + '#' + self._baseurl + hospital_url + '\n')

    def get_hospital(self):
        if os.path.exists('hospital.txt'):
            hospital_file=open('hospital.txt','r')
            content=hospital_file.readlines()
            if len(content)==156:
                hospital_file.close()
                for line in content:
                    hospital=line.split('#')[0]
                    hospital_url=line.split('#')[1][0:-1] #readline会将换行符读进来
                    #print hospital_url
                    self._hospital_dict[unicode(hospital)] = unicode(hospital_url)
            else:
                self.get_hospital_from_net()
        else:
            self.get_hospital_from_net()


    def get_appoint_url(self):
        return self._appoint_url

    def get_hospital_keys(self):
        return self._hospital_dict.keys()

    def get_consult_keys(self):
        return self._consult_dict.keys()

    def get_value_from_hosp(self,key):
        try:
            return self._hospital_dict[key]
        except KeyError,e:
            raise e

    def get_value_from_consult(self,key):
        try:
            return self._consult_dict[key]
        except KeyError,e:
            raise e

    def get_result_list(self):
        return self._search_result

    def get_consulting(self,hospital_url):
        try:
            wbtext=requests.get(hospital_url)
        except ConnectionError,e:
            raise e

        wbtext.encoding='utf-8'
        soup=BeautifulSoup(wbtext.text,'lxml',from_encoding='utf-8')
        department_list=soup.find_all(None,attrs={'class':'kfyuks_yyksdl'})
        consult_list=soup.find_all(None,attrs={'class':'kfyuks_islogin'})
        #获取每个科室下的门诊
        self._consult_dict.clear()
        for j in range(0,len(department_list)):
            tmp_consult=department_list[j]
            tmp_consult.find_next_sibling("div",attrs={'class':'kfyuks_yyksxl'})
            tmp_consult_urllist=tmp_consult.find_next_sibling("div",attrs={'class':'kfyuks_yyksxl'}).find_all('a')
            for i in range(0,len(tmp_consult_urllist)):
                self._consult_dict[department_list[j].text+'-'+tmp_consult_urllist[i].text]=self._baseurl+tmp_consult_urllist[i]['href']

    def get_weekday(self,date):
        weekday_dict={0:u'星期一',
                      1:u'星期二',
                      2:u'星期三',
                      3:u'星期四',
                      4:u'星期五',
                      5:u'星期六',
                      6:u'星期日'}
        return weekday_dict[date.weekday()]

    def search_appointment(self,consulting_url):
        self._search_result = []
        week_url=""
        for week in range(1,15):
            week_url='?week='+str(week)
            try:
                wbtext=requests.get(consulting_url+week_url)
            except ConnectionError,e:
                raise e
            wbtext.encoding='utf-8'
            soup=BeautifulSoup(wbtext.text,'lxml',from_encoding='utf-8')
            result_list=soup.find_all(None,attrs={'class':'ksorder_kyy'})
            getdate=re.compile(r'20\d\d-\d\d-\d\d')
            appoint_time=re.compile(r'\d_\d_')

            for i in range(0,len(result_list)):
                if appoint_time.search(str(result_list[i])).group().split('_')[1]=='1':
                    d_time= u'上午:'
                else:
                    d_time= u'下午:'
                date_day=getdate.search(str(result_list[i])).group(0)
                year=int(date_day.split('-')[0])
                month=int(date_day.split('-')[1])
                day=int(date_day.split('-')[2])
                tmp_date=datetime.datetime(year=year,month=month,day=day)
                weekday=self.get_weekday(tmp_date)
                temp_result=getdate.search(str(result_list[i])).group(0)+' '+d_time+str(result_list[i].text).lstrip()+' '+weekday
                self._search_result.append(temp_result)
            if self._search_result:
                self._appoint_url=consulting_url+week_url
                return
