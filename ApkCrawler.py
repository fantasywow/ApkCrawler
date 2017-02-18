# coding=utf-8

import re
import requests
import codecs

from bs4 import BeautifulSoup


def getURLContent(url):
    headers = {
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'close',
        'Referer': 'http://app.mi.com/topList',
        'Cookie': 'JSESSIONID=aaaWYqTT3MMdVfeRHjMev; __utma=127562001.883425548.1452953270.1452953270.1452953270.1; __utmc=127562001; __utmz=127562001.1452953270.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)'
    }

    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:35.0) Gecko/20100101 Firefox/35.0"

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        if r.status_code != 200:
            return None
    except requests.RequestException as e:
        print(e)
        return None
    except requests.exceptions.ConnectionError as e:
        r.status_code = "Connection refused"
        print(e)
        return None
    else:
        return r.content


def fetchApkinfoFromWebpage(weburl):
    apklist = []
    html_doc = getURLContent(weburl)
    soup = BeautifulSoup(html_doc)
    for item in soup.findAll(attrs={"class": "applist"})[0]:
        item_soup = BeautifulSoup(str(item))
        apk_name_cn = item_soup.find_all('h5')[0].get_text()
        apk_webpage = "http://app.mi.com" + item_soup.find_all('a')[0].get('href')
        downloadlist = []
        # 反复重试
        while len(downloadlist) == 0:
            html_detal = getURLContent(apk_webpage)
            soup2 = BeautifulSoup(html_detal)
            downloadlist = soup2.findAll(attrs={"class": "download"})

        downloadurl = downloadlist[0].get('href')
        apk_id = downloadurl.split("/")[-1]

        apkstring = "%s|%s|%s" % (apk_id, apk_name_cn, apk_webpage)
        # 记录写到文件里
        with codecs.open("apkinfo.txt", "a+", "utf-8") as fp:
            fp.write(apkstring)
            fp.write("\n")
        downloadApk(apk_id, apk_name_cn+".apk")
        apklist.append(apkstring)


    return apklist


def get_apk_real_downloadurl(apkid):
    apkurl_prefix = "http://app.mi.com/download/"
    s = requests.session()
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate,sdch",
        "Host": "app.mi.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }
    s.headers.update(headers)
    content = ''
    # 反复重试
    while len(content) == 0:
        resp = s.get(apkurl_prefix + str(apkid), timeout=1000, allow_redirects=False)
        content = resp.content
    print(content)
    template = '<a href="(.*?)">here</a>'
    real_url = re.compile(template)
    real_url = re.search(real_url, content.decode('utf-8')).group(1)
    return real_url


def downloadApk(apkid, apkfilename):
    s = requests.session()
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-cn,zh;q=0.8,en-us;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate,sdch",
        "Host": "app.mi.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }
    s.headers.update(headers)
    s.headers['Host'] = 'app.mi.com'
    resp = s.get('http://app.mi.com/download/' + str(apkid), timeout=100, allow_redirects=False)
    content = resp.content
    template = '<a href="(.*?)">here</a>'
    real_url = re.compile(template)
    real_url = re.search(real_url, content.decode('utf-8')).group(1)

    s.headers['Host'] = 'f3.market.xiaomi.com'
    resp = s.get(real_url, timeout=100, stream=True)
    # 根据文件大小筛选 超过一定体积就放弃下载
    if int(resp.headers['content-length']) < 1024*1024*20:
        content = resp.content
        with open(apkfilename, 'wb+') as f:
            f.write(content)



if __name__ == "__main__":
    allapklist = []
    # 选择要下载的页数
    appswebpages = ["http://app.mi.com/topList?page=%d" % i for i in range(1, 43)]

    for weburl in appswebpages:
        apklist = fetchApkinfoFromWebpage(weburl)
        allapklist.extend(apklist)
    print(len(allapklist))



