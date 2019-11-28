#!/usr/bin/env python
# coding: utf-8


from selenium import webdriver as WD
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import pandas as pd
import re
from functools import reduce
from types import SimpleNamespace
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all" # for jupyter lab

### Webdriver Chrome Options
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')
options.add_argument('--lang=ko_KR')
options.add_argument('--use-fake-ui-for-media-stream') # for media access permission
options.add_argument('--log-level=2') # to suppress info. logs
# options.add_argument("--disable-logging")
options.add_argument('''user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36''')
 # to give the false appearance of real chrome user

order='popluar' # sitePath: not typo
catDic = {# '전체보기':'','기부·후원':312,
          '테크·가전':287,'패션·잡화':288,'뷰티':311,'푸드':289,
          '홈리빙':310,'디자인소품':290,'여행·레저':296,'스포츠·모빌리티':297,
          '반려동물':308,'모임':313,'공연·컬쳐':294,'소셜·캠페인':295,'교육·키즈':309,
          '게임·취미':292,'출판':293}

main = ['serial','category','iRank','title','url','maker'] #'img'
info = ['timestamp','summary','percent','amount',
        'target','sDate','eDate','supporter','like','share']
contact = ['sDate','eDate','mail','phone','contactName','contactLink']
social = ['facebook','instagram','twitter']
website = ['site1','site2']
reward = ['rw_name','rw_price','rw_limit','rw_sold']

tC = re.compile('[^ ·:0-9a-zㄱ-ㅣ가-힣]+', re.I)
nC = re.compile('\D')

def crawl_wadiz(driverPath, url_items, crawlDT, k=20):
  #### Crawling Category Pages (k items/page)
    def crawl_wadiz_url(url, driver, k):
        iDic = {m: [] for m in main}; i = 1
        # k: 페이지당 수집 상품 수
        driver.get(url)
        driver.execute_script(f'window.scrollTo(0, {250 + 350 * k//3})')
        driver.implicitly_wait(3)
        sel_cards = 'div.ProjectCardList_list__1YBa2'
        cards = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, sel_cards+f'> div:nth-child({k}) > div > div')))
        e_url = driver.find_elements_by_css_selector(
            sel_cards + '> div.ProjectCardList_item__1owJa > div')
     
        for e in e_url:
            iRank = i
#             imgE = WebDriverWait(driver,10).until(EC.presence_of_element_located(
#                 (By.CSS_SELECTOR, f'{sel_cards} > div:nth-child({i}) > div')))
#             imgTag =imgE.find_element_by_xpath('a/div/span').get_attribute('style')
#             img = imgTag[imgTag.index('url(')+5:-3]
            textTag = e.find_element_by_css_selector(
                'div > div > div.RewardProjectCard_infoTop__1fX7c')
            url = textTag.find_element_by_xpath('a').get_attribute('href')
            serial = f'{crawlDT:%y%m%d}-{url[41:]:0>5}'
            title = tC.sub('',textTag.find_element_by_xpath('a/p/strong').text)
            category = textTag.find_element_by_xpath('div/span[1]').text
            maker = tC.sub('',textTag.find_element_by_xpath('div/span[2]').text)

            for m in main:
                iDic[m].append(locals()[m])
            i +=1
            if i > k:
                break
                
        return iDic
    
  #### Crawling Item Pages      
    def crawl_wadiz_page(c_iDic, driver, j):
        rw_name=[]; rw_price=[]; rw_limit=[]; rw_sold=[]
        df_item = pd.DataFrame()
        df_maker = pd.DataFrame()
        wDic = {'site1':0, 'site2':0}
        itemInfo = dict()
        makerInfo = dict()
        
      # URL
        url = c_iDic['url'][j]
        print(f"{j+1:-<15}\n  \'{url}\' crawling...")
        driver.get(url)

      # Date, Time  
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
      # Summary
        summary = tC.sub('',driver.find_element_by_css_selector(
            'div.campaign-summary').text)

      # Period, Target
        e_obj = driver.find_element_by_css_selector(
            '''#container > div.reward-body-wrap > div > 
               div.wd-ui-info-wrap > div.wd-ui-sub-campaign-info-container >
               div > div > section > div.wd-ui-campaign-content > div > 
               div:nth-child(4) > div > p:nth-child(1)''').text.split('    ')
        t_period = e_obj[1].replace('펀딩기간 ','').split('-')
        sDate = datetime.strptime(
            t_period[0],' %Y.%m.%d').strftime('%Y-%m-%d')
        eDate = datetime.strptime(
            t_period[1],'%Y.%m.%d').strftime('%Y-%m-%d')
        target = int(nC.sub('',e_obj[0][6:-1]))

      # Percent, Amount, #Supporter, #Like, #Share
        e_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
            '''#container > div.reward-body-wrap > div >
               div.wd-ui-info-wrap > div.wd-ui-sub-opener-info >
               div.project-state-info > div.state-box''')))
        percent = int(nC.sub('',e_content.find_element_by_css_selector(
            'p.achievement-rate > strong').text))/100
        amount = int(nC.sub('',e_content.find_element_by_css_selector(
            'p.total-amount > strong').text))
        supporter = int(nC.sub('',e_content.find_element_by_css_selector(
            'p.total-supporter > strong').text))
        like = int(nC.sub('',driver.find_element_by_css_selector(
            '#cntLike').text))
        try:
            share = int(nC.sub('',driver.find_element_by_css_selector(
            '''#campaign-support-signature > div >
               p.CampaignSupportSignature_count__2zlpi > strong''').text))
        except:
            share = 0

      # Maker-info box
        e_maker = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR,'div.maker-box')))
      # Website
        e_website = e_maker.find_elements_by_css_selector(
            'ul.website > li > a')
        k = 1
        for ref in [e.get_property('href') for e in e_website]:
            wDic[f'site{k}']=ref
            k +=1
        wNs = SimpleNamespace(**wDic)

      # SNS
        e_social = e_maker.find_elements_by_css_selector(
            'ul.social > li > a')
        sDic = {e.get_attribute('class'):e.get_property(
            'href') for e in e_social}
        sDic = {s: sDic[s] if s in sDic.keys() else 0 for s in social}
        sNs = SimpleNamespace(**sDic)

      # Mail, Phone
        e_maker.find_element_by_css_selector(
            'p.sub-title > button').click()
        e_contact = e_maker.find_element_by_css_selector(
            'div.contact-detail-info')
        mail = e_contact.find_element_by_css_selector('p.mail > a').text
        try:
            phone = int(nC.sub('',e_contact.find_element_by_css_selector(
            'p.phone > a').text))
        except:
            phone = '-'

      # Contact_etc.: Name, Link
        try:
            e_c_etc = e_contact.find_element_by_css_selector(
                'p:nth-child(3)')
            contactName = tC.sub('',
                e_c_etc.find_element_by_css_selector('span').text +': '+
                e_c_etc.find_element_by_css_selector('a').text)
            contactLink = e_c_etc.find_element_by_tag_name(
                'a').get_property('href')
        except:
            contactName = 0
            contactLink = 0

      # Reward: Name, Price, Limit_qty, Sold_qty
        e_reward = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'div.wd-ui-gift')))
        for e in e_reward.find_elements_by_css_selector('div.top-info'):
            rewardTag = e.find_element_by_css_selector('dl.reward-info')
            rw_name.append(rewardTag.find_element_by_css_selector(
                'dd > p.reward-name').text)
            rw_price.append(int(nC.sub('',
                rewardTag.find_element_by_css_selector('dt').text)))
            
            qty = int(nC.sub('',e.find_element_by_css_selector(
                    'p.reward-soldcount > strong').text))
            rw_sold.append(qty)
            result = e.find_element_by_xpath('p[1]').get_attribute('class')
            if result == 'reward-qty':
                rw_limit.append(int(nC.sub('',e.find_element_by_css_selector(
                    'p.reward-qty > strong').text)))
            elif result == 'reward-qty soldout': rw_limit.append(qty)
            elif result == 'reward-qty none': rw_limit.append(0)

     ## Item Info. DataFrame
        for r in reward:
            itemInfo[r] = locals()[r]
        for m in main:
            itemInfo[m] = [c_iDic[m][j]] * len(rw_name)
        for i in info:
            itemInfo[i] = [locals()[i]] * len(rw_name)
        
        df_item = pd.DataFrame(itemInfo).sort_values(['rw_price','rw_name'])
        df_item['rwNo'] = list(map(
            lambda x: f'{x+1:0>2}', range(len(rw_name))))
        df_item.serial = df_item.serial +'-'+ df_item.rwNo
        df_item.rwNo = list(map(lambda x : int(x),df_item.rwNo))
            
    ## Maker Info. DataFrame
        makerInfo['maker'] = [c_iDic['maker'][j]]
        for c in contact:
            makerInfo[c] = [locals()[c]]
        for s in social:
            makerInfo[s] = [eval(f'sNs.{s}')]
        for w in website:
            makerInfo[w] = [eval(f'wNs.{w}')]
        df_maker = pd.DataFrame(makerInfo)
    
     ## Check        
        if reduce(lambda x, y: x * y, map(
            lambda x: len(df_item[x])==len(rw_name), df_item.keys())) == 1:
                print(f'   <{timestamp}> complete.')

        else:
            for i in filter(
                lambda i: len(df_item[i]) != len(rw_name), info):
                print(f'   <{timestamp}> {item}')
                print(f'Error: \'{i: <11}\' not collected.')
        
        return df_item, df_maker
    
  ### Main Control
    c_iDic = {m:[] for m in main}
    df_items = pd.DataFrame()
    df_makers = pd.DataFrame()

    try:
        driver = WD.Chrome(driverPath, chrome_options = options)
        driver.maximize_window()
        driver.set_page_load_timeout(180)
        driver.implicitly_wait(2)
        
        print('-'*10)    
        for c in catDic.keys():
            c_url = f'{url_items}{catDic[c]}?order={order}'
            iDic = crawl_wadiz_url(c_url, driver, k)
            print(f' - {c}: ',len(iDic['url']),'개',sep='')
            for m in main:
                  c_iDic[m] += iDic[m]

        n = len(c_iDic['url'])
        print(f'》 총 {n}개 상품\n')

        for j in range(n):
            df_item, df_maker = crawl_wadiz_page(c_iDic, driver, j)
            df_items = pd.concat([df_items,df_item])
            
            df_makers = pd.concat([df_makers,df_maker]).sort_values(['sDate'])
            df_makers = df_makers.drop_duplicates(['maker'], keep='last')
            df_makers = df_makers.reset_index(drop=True)
            df_makers.index = df_makers.index + 1

    finally:
        driver.quit()
        print(f"\n{'=':=<20}")
        f_n = len(set(df_items.url))
        f_m = len(df_makers.maker) == len(set(df_items.maker))
        
        if not f_n == n:
            print(f'Error: {f_n}/{n} collected.')
        elif not f_m:
            print(f'Error: {set(df_items.maker)-set(df_makers.maker)} missed.')
        elif f_n * f_m:
            print('Items, Makers crawling completed.')
            
        xlsx = f'{filePath}R_{crawlDT:%y%m%d_%H%M}_Wadiz.xlsx'
        
        with pd.ExcelWriter(xlsx) as writer:
            df_items.to_excel(writer,
                sheet_name = 'R_item', header = True, index = False,
                columns = [*main,*info,*reward],
                startrow = 1, freeze_panes = (2, 0), encoding='ms949')

            df_makers.to_excel(writer,
                sheet_name = 'R_maker', header = True, index = True,
                columns = ['maker',*contact,*social,*website],
                startrow = 1, freeze_panes = (2, 0), encoding='ms949')
        
        print(f"\nfile saved: {xlsx}")
    
#### Operation
driverPath = 'C:/Users/siuser/Documents/Python Scripts/chromedriver'
filePath = 'E:/# Work/# 190925~_Wadiz Crawling/raw/Daily/'
url_items = 'https://www.wadiz.kr/web/wreward/category/'
# url_plan = 'https://www.wadiz.kr/web/wreward/collection/wadizpick'

if __name__ == '__main__':
    crawlDT = datetime.now()
    
    print('='*20,'\n[Wadiz Planned Items, Makers Crawling]┐')
    print(f"{'└ ': >40}{crawlDT:<%Y-%m-%d %H:%M>}\n{'-':-<10}")
    print(f'》 Base URL  : {url_items}')
    print(f'》 Chrome Dir: {driverPath}')
    print(f'》 Saving Dir: {filePath}')
    
    crawl_wadiz(driverPath, url_items, crawlDT, k = 5)

