
import re
import requests
import codecs

from bs4 import BeautifulSoup


def getURLContent(url):
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'close',
        'Referer': 'http://app.mi.com/topList',
        'Cookie': 'xmuuid=XMGUEST-BDD43C30-C5EE-11E6-9B29-0F5E9AEBE945; xm_user_www_num=0; lastsource=www.google.com.sg; JSESSIONID=aaabPP0ZLlDRQc0zVY6Ov; mstz=79fe2eae924d2a2e-ba0da9b90ad3370d|javascript%3Avoid(0)%3B|1604934595.83|pcpid||; mstuid=1482153986920_5787; xm_vistor=1482153986920_5787_1487426211470-1487426548064; __utma=127562001.6929003.1487419365.1487435725.1487489751.5; __utmb=127562001.2.10.1487489751; __utmc=127562001; __utmz=127562001.1487419365.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        if r.status_code != 200:
            return None
    except requests.RequestException as e:
        print(e)
        return None
    except requests.exceptions.ConnectionError as e:
        print(e)
        return None
    else:
        return r.content

def fetchApkinfoFromWebpage(weburl):
    apkList = []
    htmlDoc = getURLContent(weburl)
    soup = BeautifulSoup(htmlDoc)
    for item in soup.findAll(attrs={"class": "applist"})[0]:
        itemSoup = BeautifulSoup(str(item))
        apkNameCn = itemSoup.find_all('h5')[0].get_text()
        apkWebpage = "http://app.mi.com" + itemSoup.find_all('a')[0].get('href')
        downloadlist = []
        # 反复重试
        while len(downloadlist) == 0:
            htmlDetal = getURLContent(apkWebpage)
            soup2 = BeautifulSoup(htmlDetal)
            downloadlist = soup2.findAll(attrs={"class": "download"})

        downloadurl = downloadlist[0].get('href')
        apkId = downloadurl.split("/")[-1]

        apkString = "%s|%s|%s" % (apkId, apkNameCn, apkWebpage)
        # 记录写到文件里
        print(apkString)
        with codecs.open("apkinfo.txt", "a+", "utf-8") as fp:
            fp.write(apkString)
            fp.write("\n")
        downloadApk(apkId, apkNameCn+".apk")
        apkList.append(apkString)

    return apkList

def downloadApk(apkid, apkfilename):
    s = requests.session()
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'app.mi.com',
        'Cookie': 'xmuuid=XMGUEST-BDD43C30-C5EE-11E6-9B29-0F5E9AEBE945; xm_user_www_num=0; lastsource=www.google.com.sg; JSESSIONID=aaabPP0ZLlDRQc0zVY6Ov; mstz=79fe2eae924d2a2e-ba0da9b90ad3370d|javascript%3Avoid(0)%3B|1604934595.83|pcpid||; mstuid=1482153986920_5787; xm_vistor=1482153986920_5787_1487426211470-1487426548064; __utma=127562001.6929003.1487419365.1487435725.1487489751.5; __utmb=127562001.2.10.1487489751; __utmc=127562001; __utmz=127562001.1487419365.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Cache-Control': 'no-cache'
    }

    s.headers.update(headers)
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
    print("总共获取记录："len(allapklist))



