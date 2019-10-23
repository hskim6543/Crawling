#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from selenium import webdriver as WD
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import OrderedDict
from datetime import datetime
import pandas as pd
from functools import reduce
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"


# In[ ]:


social = ['facebook','instagram','twitter']
contact = ['mail','phone','contactName','contactLink']
info = ['serial','datetime','iRank','category','item','title','summary',
        'percent','amount','target','sDate','eDate','supporter','like','share',
        'maker','site1','site2',*social,*contact,'url','img']

l_iRank=[]; l_url=[]; l_img=[]; l_serial=[]
l_category=[]; l_item=[]; l_title=[]; l_category=[]; l_summary=[]
l_percent=[]; l_amount=[]; l_target=[]; l_sDate=[]; l_eDate=[]
l_supporter=[]; l_like=[]; l_share=[]; l_datetime=[]; l_maker=[]
l_site1=[]; l_site2=[]; l_facebook=[]; l_instagram=[]; l_twitter=[]
l_mail=[]; l_phone=[]; l_contactName=[]; l_contactLink=[]


# In[ ]:


def crawl_wadiz(driverPath, url_wadiz, crawlDT):
    
    def crawl_url_wadiz(url_wadiz, driver):
        driver.get(url_wadiz)
        wait = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR,
                 '''div.ProjectCardList_container__3Y14k > div >
                    div:nth-child(30)''')))
        driver.execute_script("window.scrollTo(0, 250)")
        e_url = driver.find_elements_by_xpath(
                "//div[@class='ProjectCardList_item__1owJa']/div/a")
        i = 1
        for e in e_url:
            l_url.append(e.get_attribute('href'))
            l_iRank.append(i)
            l_serial.append(f'{crawlDT:%y%m%d%H%M}-{i:0>2}')
            img = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,            
                    'div.CommonProjectCard_rect__3A4Yf > span')
                    )).get_attribute('style')
            l_img.append(img[img.index('image: url(')+12:-3])
            driver.execute_script(
                f'window.scrollTo(0, {250 + 350 * len(l_img)//3})')
            driver.implicitly_wait(0.5)
            i +=1
    
    def crawl_page_wadiz(page, driver, j):
        print(f"{j:-<15}\n  \'{page}\' open")
        driver.get(page)

      ## Date, Time  
        now = datetime.now()
        l_datetime.append(now)

      ## Title, Item, Category, Summary
        e_title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
                'div.reward-header')))
        item = e_title.find_element_by_css_selector(
            'p.title-info > strong').text
        l_item.append(item)
        print(f'   {item} crawling start')
        l_category.append(e_title.find_element_by_css_selector(
            'p.title-info > em').text)
        l_title.append(e_title.find_element_by_tag_name(
            'h2.title > a').text)
        l_summary.append(driver.find_element_by_class_name(
            'campaign-summary').text)

      ## Period, Target
        e_obj = driver.find_element_by_css_selector(
            '''#container > div.reward-body-wrap > div > div.wd-ui-info-wrap > 
               div.wd-ui-sub-campaign-info-container > div > div > section > 
               div.wd-ui-campaign-content > div > div:nth-child(4) > div >
               p:nth-child(1)''').text.split('    ')
        t_period = e_obj[1].replace('펀딩기간 ','').split('-')
        l_sDate.append(datetime.strptime(t_period[0],' %Y.%m.%d'))
        l_eDate.append(datetime.strptime(t_period[1],'%Y.%m.%d'))
        l_target.append(int(e_obj[0][6:-1].replace(',','')))

      ## Percent, Amount, #Supporter, #Like, #Share
        e_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR,
            '''#container > div.reward-body-wrap > div > div.wd-ui-info-wrap >
               div.wd-ui-sub-opener-info > div.project-state-info >
               div.state-box''')))
        l_percent.append(e_content.find_element_by_css_selector(
            'p.achievement-rate > strong').text)
        l_amount.append(int(e_content.find_element_by_css_selector(
            'p.total-amount > strong').text.replace(',','')))
        l_supporter.append(int(e_content.find_element_by_css_selector(
            'p.total-supporter > strong').text.replace(',','')))
        l_like.append(int(driver.find_element_by_css_selector(
            '#cntLike').text.replace(',','')))
        l_share.append(int(driver.find_element_by_css_selector(
            '''#campaign-support-signature > div >
               p.CampaignSupportSignature_count__2zlpi
               > strong''').text.replace('명','').replace(',','')))

      ## Maker
        e_maker = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.maker-box')))
        l_maker.append(e_maker.find_element_by_css_selector('p.name').text)

      ### Website
        e_website = e_maker.find_elements_by_css_selector(
            'ul.website > li > a')
        wList = [e.get_property('href') for e in e_website]
        try:
            l_site1.append(wList[0])
            try:
                l_site2.append(wList[1])
            except:
                l_site2.append('-')
        except:
            l_site1.append('-')
            l_site2.append('-')

      ### SNS
        e_social = e_maker.find_elements_by_css_selector('ul.social > li > a')
        sDic = {e.get_attribute('class'):e.get_property(
            'href') for e in e_social}
        for s in social:
            if s in sDic.keys():
                globals()[f'l_{s}'].append(sDic[s])
            else:
                globals()[f'l_{s}'].append('-')

      ### Mail, Phone
        e_maker.find_element_by_css_selector('p.sub-title > button').click()
        e_contact = e_maker.find_element_by_css_selector(
            'div.contact-detail-info')

        l_mail.append(e_contact.find_element_by_css_selector(
            'p.mail > a').get_attribute('href').replace('mailto:',''))
        l_phone.append(e_contact.find_element_by_css_selector(
            'p.phone > a').get_attribute('href').replace(
            'tel:','').replace('-','').replace(' ','').replace('.',''))

      ### Contact_etc.: Name, Link
        try:
            e_c_etc = e_contact.find_element_by_css_selector(
                'p:nth-child(3)')
            l_contactName.append(e_c_etc.find_element_by_css_selector(
                'span').text + '_' +
                e_c_etc.find_element_by_css_selector('a').text)
            l_contactLink.append(e_c_etc.find_element_by_tag_name(
                'a').get_property('href'))
        except:
            l_contactName.append('-')
            l_contactLink.append('-')

        print(f'   {now:%y/%m/%d %H:%M:%S}_{item} complete')
    
    driver = WD.Chrome(driverPath)
    driver.maximize_window()
    driver.set_page_load_timeout(180)
    driver.implicitly_wait(2)
    crawl_url_wadiz(url_wadiz, driver)

    try:
        print('='*10)
        print(f'''{crawlDT:<%Y-%m-%d %H:%M>}┐\n{
            '└ ': >20}Wadiz Crawling Start: {len(l_url)}개\n''')
        j = 1
        for page in l_url:
            crawl_page_wadiz(page, driver, j)
            j +=1

    finally:
        driver.quit()
        itemList = {i:globals()[f'l_{i}'] for i in info}
        for i in filter(lambda i: len(itemList[i]) != len(l_url), info):
            print(f'Error: {i}: {len(itemList[i])}/{len(l_url)} collected.')
        print('='*10)

        if reduce(lambda x, y: x * y, 
              map(lambda x: len(itemList[x])==len(l_url), itemList.keys()))==1:
            df = pd.DataFrame(itemList)
            df = df.set_index('serial')
            print(f'''{crawlDT:<%Y-%m-%d %H:%M>}┐\n{
                '└ ': >20}Wadiz planned item crawling complete''')
    return df


# In[ ]:


driverPath = 'C:/Users/siuser/Documents/Python Scripts/chromedriver'
csvPath = 'E:/# Work/# 190925~_Wadiz Crawling/raw/'
url_wadiz = '''https://www.wadiz.kr/web/wreward/collection/wadizpick?
            keyword=&endYn=ALL&order=recommend'''
crawlDT = datetime.now()

if __name__ == '__main__':
    df = crawl_wadiz(driverPath, url_wadiz, crawlDT)

    df.datetime = [s.strftime('%Y-%m-%d %H:%M:%S') for s in df.datetime]
    df.sDate = [s.strftime('%Y-%m-%d') for s in df.sDate]
    df.eDate = [s.strftime('%Y-%m-%d') for s in df.eDate]
    df.to_csv(f'{csvPath}{crawlDT:%y%m%d_%H%M}_Wadiz.csv',
              mode='w', encoding='ms949')

    print(f"\'{crawlDT:%y%m%d_%H%M}_Wadiz.csv\' file saved.")

