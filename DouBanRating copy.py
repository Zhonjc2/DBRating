import os
import time
import csv
import requests as re
import bs4
import matplotlib.pyplot as mp
import jieba as fc
import wordcloud as wc
from matplotlib.font_manager import FontProperties

abs_path=os.path.abspath(__file__)
res_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/PythonResource/'
abs_dir=os.path.dirname(__file__)+'/'

def get_topic(soup):
    topic = soup.find('div', id='content').h1.string
    return topic

def get_keywords(soup):
    keywords=[]
    attrs=soup.find('div',class_='movie-summary').find('span',class_='attrs')
    print(attrs['class'])
    for attr in attrs.find_all('p'):
        print(attr)
        for value in attr.find_all('a'):
            keywords.append(value.string)
    return keywords

    

def connect(start, did, limit):
    headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                      'Version/15.4 Safari/605.1.15'}
    link='https://movie.douban.com/subject/' + did +'/comments'
    params={
        'start':start,
        'limit':limit,
        'status':'P',
        'sort':'new_score'
    }
    print('Current Link:'+link)
    print('Current Params:',params)
    try:
        db = re.get(link, headers=headers,params=params)
        db.raise_for_status()
    except Exception as ex:
        print('ID无效或网络不佳')
        print('该页采集失败')
        return None
    if '200' not in str(db):
        print('ID无效或网络不佳') 
        return None
    # print('获取到HTML：',db.text)
    return bs4.BeautifulSoup(db.text, 'html.parser')


def rating_view(topic, rating_list):
    if type(rating_list) != list:
        print('类型错误')
        return None
    print('可视化评级...')
    rating_list = [rate[7:8] for rate in rating_list]
    rating_list.sort(reverse=True)
    ratingdict = {}
    for rate in rating_list:
        ratingdict[rate] = ratingdict.get(rate, 0) + 1
    global res_path
    font = FontProperties(fname=res_path+'smr.otf', size=10)
    for i in range(5,0,-1):
        if ratingdict.get(str(i),0)==0:
            ratingdict[str(i)]=0
    print(ratingdict)
    mp.plot([5, 4, 3, 2, 1], ratingdict.values())
    mp.title(topic[0:-2] + ' 评级折线图', fontproperties=font)
    mp.xlabel('评级', fontproperties=font)
    mp.ylabel('人数', fontproperties=font)
    mp.xticks([5, 4, 3, 2, 1])
    mp.show()
    labels = ['力荐', '推荐', '还行', '较差', '很差']
    mp.pie(ratingdict.values(), labels=[5, 4, 3, 2, 1], autopct='%.2f%%')
    mp.title(topic[0:-2] + ' 评级比例图', fontproperties=font)
    mp.show()

def saveCSV(topic,list):
    global abs_dir
    with open(abs_dir+topic+' CSV.csv','a',encoding='utf8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(list)
        print('写入',list)

def save_comment(topic:str,name:str='',star:str='',comment:str=''):
    global abs_dir
    with open(abs_dir+topic+'.txt','a',encoding='utf8',newline='') as f:
        f.write(name+'\n'+star+'\n'+comment+'\n\n')
    with open(abs_dir+topic+'纯净版.txt','a',encoding='utf8',newline='') as f:
        f.write(comment+'\n')
    

def get_rating(soup):
    topic = get_topic(soup)
    print('开始分析 ' + topic+'...')
    time.sleep(5)
    divList = soup.find_all(class_='comment-item')
    rating_list = []
    for div in divList:
        if len(div.find_all(class_='comment-content'))==0:
            print('当前div无短评，跳过...')
            continue
        avatar = div.find('div', class_='avatar')
        if type(avatar) != bs4.element.Tag:
            continue
        title = avatar.find('a')['title']
        try:
            ratingSpan = div.find('span', class_='rating')  # 注意find方法返回的是一个Tag对象。
            rating = ratingSpan['class']
            rating.insert(0, title)
            print(rating)
            saveCSV(topic,rating)
            save_comment(topic,rating[0],rating[1],div.find('span',class_='short').string)
            rating_list.append(rating)
        except TypeError:
            print(title + '没有评级该书影音')
            save_comment(topic,title,'N/A',div.find('span',class_='short').string)
    return [rate[1] for rate in rating_list]

def words_frequency(shorts:list,dict=[]):
    global res_path
    with open(res_path+'stop_words.txt','r',encoding='utf8',newline='') as f:
        stop_words=f.readlines()
    words_frequency={}
    for short in shorts:
        words_list=fc.lcut(short)
        fc.load_userdict(dict)
        for word in words_list:
            if word not in stop_words and len(word)>1:
                words_frequency[word]=words_frequency.get(word,0)+1
    return words_frequency

def wordcloud_generate(wfrequency,name:str='wcloud.png'):
    print('生成词云...')
    global res_path,abs_dir
    wcloud=wc.WordCloud(
        font_path=res_path+'smr.otf',
        width=5000,
        height=2000
    )
    wcloud.generate_from_frequencies(wfrequency)
    wcloud.to_file(abs_dir+name)

did = input('请输入豆瓣ID  ')
quantity=eval(input('请输入短评分析量级，单位为50  '))
rate_list = []
all = 0
step=50
soup=None
for i in range(quantity):
    print('暂缓...')
    time.sleep(2)
    soup = connect(step * i, did, step)
    if soup is None: continue
    rating_list = get_rating(soup)
    if len(rating_list) == 0: continue
    rate_list = rate_list + rating_list
    all += step
print('总收集短评共' + str(all) + '条')
rating_view(get_topic(soup), rate_list)

keywords=[]
keywords.append(get_topic(soup)[:-3])
keywords.extend(get_keywords(soup))
print('收集到关键词',keywords)

with open(abs_dir+get_topic(soup)+'纯净版.txt','r',encoding='utf8',newline='') as f:
    wordcloud_generate(words_frequency(f.readlines(),keywords),get_topic(soup)[:-2]+' 词云.png',dict=keywords)


# Your Name 
# https://movie.douban.com/subject/26683290/comments?start=20&status=P&sort=new_score
# https://movie.douban.com/subject/26683290/comments?sort=new_score&status=P

# Sample Div
# <div class="comment-item" data-cid="1081581750">
# <div class="avatar">
# <a href="https://www.douban.com/people/cevia/" title="银河系漫游指南">
# <img class="" src="https://img2.doubanio.com/icon/u51765994-12.jpg"/>
# </a>
# </div>
# <div class="comment">
# <h3>
# <span class="comment-vote">
# <span class="votes vote-count">21064</span>
# <input type="hidden" value="1081581750">
# <a class="j a_show_login" data-id="1081581750" href="javascript:;" onclick="">有用</a>
# <!-- 删除短评 -->
# </input></span>
# <span class="comment-info">
# <a class="" href="https://www.douban.com/people/cevia/">银河系漫游指南</a>
# <span>看过</span>
# <span class="allstar50 rating" title="力荐"></span>
# <span class="comment-time" title="2016-09-05 21:17:35">
#                     2016-09-05 21:17:35
#                 </span>
# </span>
# </h3>
# <p class="comment-content">
# <span class="short">这部片深刻地告诉我们 一个有好剧本的诚哥有多可怕 ☄</span>
# </p>
# </div>
# </div>

# https://movie.douban.com/subject/1292052/comments?start=600&limit=300&status=P&sort=new_score
# https://movie.douban.com/subject/1292052/comments?start=600&limit=300&status=P&sort=new_score

# Cookie , 'Cookie': '__utma=30149280.1110433273.1651803109.1651935121'
                                                                # '.1651938875.6; __utmb=30149280.10.10.1651938875; '
                                                                # '__utmc=30149280; '
                                                                # '__utmz=30149280.1651803109.1.1.utmcsr=('
                                                                # 'direct)|utmccn=(direct)|utmcmd=(none); ck=tpir; '
                                                                # 'dbcl2="109989483:Q3zohUhcSU8"; __utmt=1; ap_v=0,'
                                                                # '6.0; ct=y; '
                                                                # '__gpi=UID=000005335086a375:T=1651918865:RT=1651918865'
                                                                # ':S=ALNI_MbIEqWnv0lVKtej-FubDQ57RYUl3A; '
                                                                # '__gads=ID=0cfdf18c91269b42-223f0ea710d3003a:T'
                                                                # '=1651803132:RT=1651803132:S'
                                                                # '=ALNI_MY6MvateJA1Zi7lDFpgAWJweWfOag; bid=ZVy2EUECzOg; '
                                                                # 'll="118108"'