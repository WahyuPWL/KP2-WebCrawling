from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework import status
from rest_framework import viewsets
from rest_framework import filters
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import TimeoutException,NoSuchElementException,ElementNotInteractableException
from selenium.webdriver.common.keys import Keys
import json

class paperList(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = paper.objects.all()
    serializer_class = paperSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['author']

def progressPercentage(current,total):
    fraction = current/total
    if current == total:
        print('\rProgress: ','[{:>1.2%}]'.format(fraction))
    else:
        print('\rProgress: ','[{:>1.2%}]'.format(fraction),end='')

def crawl(page_num, count_items, driver, url):
    result = [] #paper yang diambil
    if count_items == 0:
        print('No target found')
        return []
    for num in range(page_num):
        items = driver.find_elements_by_css_selector('.uk-description-list-line') #induk element dari target items
        for i in range(len(items)):
            progressPercentage((i+1)+(num*10), count_items)
            desc1 = items[i].find_elements_by_css_selector('.paper-link')
            desc2 = items[i].find_elements_by_css_selector('.indexed-by')
            result.append([
                desc1[0].text,                  #Judul
                desc1[0].get_attribute("href"), #Document Link
                desc2[0].text                   #Detail
                ])
        if(num != page_num-1):
            url = url.replace('&page=' + str(num+1), '&page=' + str(num+2)) #ganti halaman
            driver.get(url)
    return result

def AddDataSinta(listDosen, options):
    #Setup the driver for opening url
    driver = webdriver.Firefox(options=options)
    for dosen in range(len(listDosen)):
        print("Start crawling : "+ listDosen[dosen] +" in Sinta2")
        try:
            # Pembanding dengan database
            savedPaper = paper.objects.filter(author=listDosen[dosen]).values_list('judul',flat=True)
            url = "http://sinta2.ristekdikti.go.id/affiliations/detail?q="+ listDosen[dosen].replace(" ","+") +"&search=1&view=authors&id=27&sort=year2"

            driver.get(url)
            authors = driver.find_elements_by_css_selector('a[href*="/authors/detail/?id="]')
            print("Searching ...")
            if len(authors) == 0: #Fungsi telah digantikan general exception, bisa dihapus
                continue
            temp_url = authors[0].get_attribute("href") # url dasar untuk digunakan di WoS dan Scopus

            #WoS Documents
            url = temp_url.replace('overview','documentswos')
            url += "&page=1"
            driver.get(url)
            print("Found possible target!")
            page = driver.find_elements_by_css_selector('div[class*="uk-width-large-1-2 table-footer"')
            if page is not None:
                page_num = int((page[0].text).split()[3])
                count_items = int((page[0].text).split()[8])
            target=crawl(page_num, count_items, driver, url) #memulai fungsi crawl target

            #menyimpan ke database
            if len(target) != 0:
                print('Saving...')
            for i in range(len(target)):
                progressPercentage(i+1,len(target))
                must_it_be_added = True
                for j in savedPaper:
                    if target[i][0] in j:
                        must_it_be_added = False
                        break
                    elif j in target[i][0]:
                        must_it_be_added = False
                        break
                if must_it_be_added:
                    file=paper(
                        author = listDosen[dosen],
                        judul = target[i][0],
                        link = target[i][1],
                        detail = target[i][2]
                    )
                    file.save()

            #Scopus Documents
            url = temp_url.replace('overview','documentsscopus')
            url += "&page=1"
            driver.get(url)
            print("Found possible target!")
            page = driver.find_elements_by_css_selector('div[class*="uk-width-large-1-2 table-footer"')
            if page is not None:
                page_num = int((page[0].text).split()[3])
                count_items = int((page[0].text).split()[8])
            target=crawl(page_num, count_items, driver, url) #memulai fungsi crawl target

            if len(target) != 0:
                print('Saving...')
            else:
                print('\n')
            for i in range(len(target)):
                progressPercentage(i+1,len(target))
                must_it_be_added = True
                for j in savedPaper:
                    if target[i][0] in j:
                        must_it_be_added = False
                        break
                    elif j in target[i][0]:
                        must_it_be_added = False
                        break
                if must_it_be_added:
                    file=paper(
                        author = listDosen[dosen],
                        judul = target[i][0],
                        link = target[i][1],
                        detail = target[i][2]
                    )
                    file.save()
            print("Completed crawled paper done for : "+ listDosen[dosen]+"\n")
            with open("Sinta2.log", "a") as file:
                file.write("%s\n" % listDosen[dosen])
        except Exception:
            print(str(Exception))
            print("Failed to Obtain!\n")
    driver.quit()
    return None

def AddDataIeee(listDosen, options, timeout):
    driver = webdriver.Firefox(options=options)
    wait = WebDriverWait(driver, timeout)
    wait_error = WebDriverWait(driver, 2)
    for dosen in range(len(listDosen)):
        try:
            result = []
            print("Start crawling : "+ listDosen[dosen] +" in Ieee")
            savedPaper = paper.objects.filter(author = listDosen[dosen]).values_list('judul',flat=True)
            url="https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText="+ listDosen[dosen].replace(' ','+')
            while True:
                driver.get(url)
                while True:
                    elements = driver.find_elements_by_xpath('//div/p[contains(text(),"Getting results...")]')
                    if len(elements) == 0:
                        break
                try:
                    elements = wait_error.until(EC.presence_of_element_located((By.XPATH, '//div/p[contains(text(),"Something went wrong in getting results, please try again later.")]')))
                    url=driver.current_url
                except TimeoutException:
                    break
            try:
                elements = wait.until(EC.presence_of_element_located((By.XPATH , '//p[@class="author"]')))
            except TimeoutException:
                print('No target found\n')
                continue
            print("Searching ...")
            while True:
                try:
                    loadMore = driver.find_elements_by_css_selector('button.loadMore-btn')
                    if len(loadMore)!= 0:
                        loadMore.click()
                        try:
                            loadMore = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'button.loadMore-btn')))
                        except TimeoutException:
                            break
                    else:
                        break
                except NoSuchElementException:
                    None
            print("Found possible target!")
            items = driver.find_elements_by_css_selector('div.List-results-items')
            print('Crawling...')
            for i in range(len(items)):
                progressPercentage(i+1,len(items))
                desc1 = items[i].find_element_by_css_selector('h2[_ngcontent-c19=""] a')
                desc2 = items[i].find_element_by_css_selector('p.author')
                desc3 = items[i].find_element_by_css_selector('div.description a')
                desc4 = items[i].find_element_by_css_selector('div.publisher-info-container')
                result.append([
                    desc1.text,                 #Judul
                    desc1.get_attribute("href"),#Document Link
                    desc2.text,                 #Authors
                    desc3.text,                 #Source Name
                    desc3.get_attribute("href"),#Link Source
                    desc4.text                  #Detail
                ])
            print("Saving...")
            for i in range(len(result)):
                progressPercentage(i+1,len(result))
                must_it_be_added = True
                for j in savedPaper:
                    if result[i][0] in j[0]:
                        must_it_be_added = False
                        break
                    elif j[0] in result[i][0]:
                        must_it_be_added = False
                        break
                if must_it_be_added:
                    file = paper(
                        author = listDosen[dosen],
                        judul = result[i][0],
                        authors = result[i][2],
                        link = result[i][1],
                        source = result[i][3],
                        linksource = result[i][4],
                        detail = result[i][5]
                    )
                    file.save()
            print("Completed crawled paper done for : "+ listDosen[dosen] +"\n")
            with open("Ieee.log", "a") as file:
                file.write("%s\n" % listDosen[dosen])
        except Exception:
            print(str(Exception))
            print("Failed to Obtain!\n")
    driver.quit()
    return None

def AddDataDoaj(listDosen, options, timeout):
    driver = webdriver.Firefox(options=options)
    wait = WebDriverWait(driver, timeout)
    for dosen in range(len(listDosen)):
        try:
            savedPaper = paper.objects.filter(author=listDosen[dosen]).values_list('judul',flat=True)
            url="https://doaj.org/search?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22"+ listDosen[dosen].replace(' ','%20') +"%22%2C%22default_operator%22%3A%22AND%22%7D%7D%2C%22from%22%3A0%2C%22size%22%3A10%7D"
            driver.get(url)
            result = []
            print("Start crawling : "+ listDosen[dosen] +" in Doaj")
            while True:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.span10')))
                    break
                except TimeoutException:
                    break
            page = driver.find_elements_by_css_selector('div.span4 p')
            count_items = int((page[0].text).split()[4])
            if len(page) == 0:
                print('No target found\n')
                continue
            print('Crawling...')
            for count in range(count_items):
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.span10')))
                except TimeoutException:
                    break
                elements = driver.find_elements_by_css_selector('div.span10')
                for i in range(len(elements)):
                    progressPercentage((i+1)+(count*10), count_items)
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.span10')))
                    except TimeoutException:
                        continue
                    check_is_ok = False
                    check_aspect1 = "Universitas Muhammadiyah Surakarta"
                    check_aspect2 = listDosen[dosen]
                    check_aspect3 = "UMS"
                    temp_url = driver.current_url
                    items = driver.find_elements_by_css_selector('div.span10')
                    url = items[i].find_element_by_css_selector('a').get_attribute("href")
                    driver.get(url)
                    #memeriksa institusi penerbit
                    try:
                        check = driver.find_elements_by_css_selector('div.row-fluid div.span5 div.box p')[4].text
                        if check_aspect1 in check:
                            check_is_ok = True
                        elif check_aspect3 in check:
                            check_is_ok = True
                    except NoSuchElementException:
                        try:
                            checks = driver.find_elements_by_css_selector('div.row-fluid div.span5 p')
                            for i in range(len(checks)):
                                check = checks[i].find_element_by_css_selector('em')
                                if check_aspect2 in check.text and check_aspect1 in check.text:
                                    check_is_ok = True
                                elif check_aspect2 in check.text and check_aspect3 in check.text:
                                    check_is_ok = True
                        except NoSuchElementException:
                            None
                    driver.get(temp_url)
                    if check_is_ok:
                        try:
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.span10')))
                        except TimeoutException:
                            continue
                        items = driver.find_elements_by_css_selector('div.span10')
                        desc1 = items[i].find_element_by_css_selector('span.title a')
                        desc2 = items[i].find_element_by_css_selector('em')
                        desc3 = items[i].find_elements_by_css_selector('a')[1]
                        result.append([
                            desc1.text,                 #Judul
                            desc1.get_attribute("href"),#Document Link
                            desc2.text,                 #Authors
                            desc3.text,                 #Source Name
                            desc3.get_attribute("href"),#Link source
                            items[i].text.split('\n')[2]#Detail
                        ])
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.span10')))
                except TimeoutException:
                    break
                nextPage = driver.find_elements_by_css_selector('span.icon-arrow-right')
                if len(nextPage)==0:
                    break
                else:
                    nextPage[0].click()
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.facetview_searching[style="display: block;"]')))
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'div.facetview_searching[style="display: none;"]')))
                    except TimeoutException:
                        None
            print("Saving...")
            for i in range(len(result)):
                progressPercentage(i+1,len(result))
                must_it_be_added = True
                for j in savedPaper:
                    if result[i][0] in j[0]:
                        must_it_be_added = False
                        break
                    elif j[0] in result[i][0]:
                        must_it_be_added = False
                        break
                if must_it_be_added:
                    file=paper(
                        author = listDosen[dosen],
                        judul = result[i][0],
                        authors = result[i][2],
                        link = result[i][1],
                        source = result[i][3],
                        linksource = result[i][4],
                        detail = result[i][5]
                    )
                    file.save()
            print("Completed crawled paper done for : "+ listDosen[dosen]+"\n")
            with open("Doaj.log", "a") as file:
                file.write("%s\n" % listDosen[dosen])
        except Exception:
            print(str(Exception))
            print("Failed to Obtain!\n")
    driver.quit()
    return None

def AddRG(listDosen, options, timeout):
    for dosen in range(len(listDosen)):
        savedPaper = paper.objects.filter(author=listDosen[dosen]).values_list('judul',flat=True)
        try:
            driver = webdriver.Firefox(options=options)
            wait = WebDriverWait(driver, timeout)
            result = []
            print("Start crawling : "+ listDosen[dosen] +" in ResearchGate")
            element="https://www.researchgate.net"
            driver.get(element)
            element = driver.find_element_by_css_selector('a[href*="directory/profiles"]')
            oldUrl=driver.current_url
            element.click()
            try:
                element = wait.until(lambda driver: driver.current_url != oldUrl)
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'form.c-search-magnifier input[name="query"]')))
            except (TimeoutException,NoSuchElementException):
                driver.quit()
            element = driver.find_element_by_css_selector('form.c-search-magnifier input[name="query"]')
            element.send_keys(listDosen[dosen])
            element.send_keys(Keys.RETURN)
            print("Searching ...")
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.menu-content a.menu-item[href*="search/authors?"]')))
            except (TimeoutException,NoSuchElementException):
                driver.quit()
            for i in range(2):
                elements = driver.find_elements_by_css_selector('div.menu-content a.menu-item[href*="search/authors?"]')
                if elements[0] is not None:
                    elements[0].click()
            institutions=driver.find_elements_by_css_selector('div.nova-v-person-item[itemtype*="http://schema.org"]')
            num_inst = 0
            for i in range(len(institutions)):
                wanted = "Universitas Muhammadiyah Surakarta"
                comparison = institutions[i].find_element_by_css_selector('div.nova-v-person-item__stack-item div.nova-v-person-item__info-section li.nova-e-list__item span').text
                if wanted == comparison:
                    num_inst = i
                    break
            try:
                element=wait.until(lambda driver: driver.current_url != oldUrl)
                element=wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div[itemprop="name"] a[href*="profile/'+listDosen[dosen].replace(' ','_')+'"]')))
            except (TimeoutException,NoSuchElementException):
                driver.quit()
            try:
                element = institutions[num_inst].find_element_by_css_selector('a[href*="profile/'+listDosen[dosen].replace(' ','_')+'"]')
                print("Found possible target!")
            except (NoSuchElementException,IndexError):
                print("No target found\n")
                driver.quit()
                continue
            element.click()
            try:
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR , 'div.nova-o-stack__item div.nova-v-publication-item__stack--gutter-m div[itemprop*="headline"] a')))
            except (TimeoutException,NoSuchElementException):
                driver.quit()
            try:
                element = driver.find_element_by_css_selector('span.gtm-cookie-consented')
                if element is not None:
                    element.click()
            except(ElementNotInteractableException,TimeoutException):
                None
            elements = driver.find_elements_by_css_selector('div.nova-o-stack__item div.nova-v-publication-item__body div.nova-v-publication-item__stack--gutter-m')
            print('Crawling...')
            for i in range(len(elements)):
                progressPercentage(i+1,len(elements))
                try:
                    desc1 = elements[i].find_element_by_css_selector('div[itemprop*="headline"] a')
                    desc2 = elements[i].find_element_by_css_selector('ul.nova-v-publication-item__person-list')
                    desc31 = None
                    desc32 = None
                    try:
                        desc31 = elements[i].find_element_by_css_selector('span[priority="secondary"]')
                        desc32 = elements[i].find_element_by_css_selector('li.nova-v-publication-item__meta-data-item')
                        desc3 = desc31.text+ ';' +desc32.text
                    except NoSuchElementException:
                        None
                    if desc31 is None and desc32 is None:
                        desc3 = None
                    elif desc31 is None:
                        desc3 = desc32.text
                    elif desc32 is None:
                        desc3 = desc31.text
                except NoSuchElementException:
                    continue
                result.append([
                    desc1.text,                     #Judul
                    desc1.get_attribute('href'),    #Document Link
                    (desc2.text).replace('\n',', '),#Authors
                    desc3                           #Detail
                ])
            print("Saving...")
            for i in range(len(result)):
                progressPercentage(i+1,len(result))
                must_it_be_added = True
                for j in savedPaper:
                    if result[i][0] in j:
                        must_it_be_added = False
                        break
                    elif j in result[i][0]:
                        must_it_be_added = False
                        break
                if must_it_be_added:
                    file=paper(
                        author=listDosen[dosen],
                        judul=result[i][0],
                        authors=result[i][2],
                        link=result[i][1],
                        detail=result[i][3]
                    )
                    file.save()
            print("Completed crawled paper done for : "+ listDosen[dosen] +"\n")
            with open("Rg.log", "a") as file:
                file.write("%s\n" % listDosen[dosen])
            driver.quit()
        except Exception:
            print(str(Exception))
            print("Failed to Obtain!\n")
    return None

def addSinta(request):
    listDosen=["Heru Supriyono","Husni Thamrin","Fajar Suryawan","Bana Handaga"]
    options = Options()
    options.headless = True #False, untuk menamplikan GUI firefox
    waiting_time = 10 #detik,mengatur timeout pada tiap menunggu element yang dicari
    AddDataSinta(listDosen, options,waiting_time)
    return redirect('../paper/')

def addIeee(request):
    listDosen=["Heru Supriyono","Husni Thamrin","Fajar Suryawan","Bana Handaga"]
    options = Options()
    options.headless = True #False, untuk menamplikan GUI firefox
    waiting_time = 10 #detik,mengatur timeout pada tiap menunggu element yang dicari
    AddDataIeee(listDosen, options,waiting_time)
    return redirect('../paper/')

def addDoaj(request):
    listDosen=["Heru Supriyono","Husni Thamrin","Fajar Suryawan","Bana Handaga"]
    options = Options()
    options.headless = True #False, untuk menamplikan GUI firefox
    waiting_time = 10 #detik,mengatur timeout pada tiap menunggu element yang dicari
    AddDataDoaj(listDosen, options,waiting_time)
    return redirect('../paper/')

def addRg(request):
    listDosen=["Heru Supriyono","Husni Thamrin","Fajar Suryawan","Bana Handaga"]
    options = Options()
    options.headless = True #False, untuk menamplikan GUI firefox
    waiting_time = 10 #detik,mengatur timeout pada tiap menunggu element yang dicari
    AddRG(listDosen, options,waiting_time)
    return redirect('../paper/')

def fixing(listDosen, options, waiting_time):
    is_fixed = False
    fix_param = 0
    with open("Sinta2.log", "r+") as file:
        completed_sinta2 = file.read().split('\n')
        listDosenSinta2 = [i for i in listDosen if i not in completed_sinta2]
        if len(listDosenSinta2) != 0:
            print("Fixing data on Sinta2")
            AddDataSinta(listDosenSinta2, options)
        else:
            fix_param+=1
    with open("Ieee.log", "r+") as file:
        completed_Ieee = file.read().split('\n')
        listDosenIeee = [i for i in listDosen if i not in completed_Ieee]
        if len(listDosenIeee) != 0:
            print("Fixing data on Ieee")
            AddDataIeee(listDosenIeee, options,waiting_time)
        else:
            fix_param+=1
    with open("Doaj.log", "r+") as file:
        completed_Doaj = file.read().split('\n')
        listDosenDoaj = [i for i in listDosen if i not in completed_Doaj]
        if len(listDosenDoaj) != 0:
            print("Fixing data on Doaj")
            AddDataDoaj(listDosenDoaj, options,waiting_time)
        else:
            fix_param+=1
    with open("Rg.log", "r+") as file:
        completed_Rg = file.read().split('\n')
        listDosenRg = [i for i in listDosen if i not in completed_Rg]
        if len(listDosenRg) != 0:
            print("Fixing data on ResearchGate")
            AddRG(listDosenRg, options,waiting_time)
        else:
            fix_param+=1
    if fix_param == 4:
        is_fixed = True
    return is_fixed

def is_need_fixing(request):
    listDosen=["Heru Supriyono","Husni Thamrin","Fajar Suryawan","Bana Handaga"]
    options = Options()
    options.headless = True #False, untuk menampilkan GUI firefox
    waiting_time = 10 #detik,mengatur timeout pada tiap menunggu element yang dicari
    while True: #Dapat diganti dengan perulangan for
        is_fixed = fixing(listDosen, options, waiting_time)
        if is_fixed:
            break
    return redirect('../paper/')

def Main(request):
    listDosen=["Heru Supriyono","Husni Thamrin","Fajar Suryawan","Bana Handaga"]
    options = Options()
    options.headless = True #False, untuk menampilkan GUI firefox
    waiting_time = 2 #detik,mengatur timeout pada tiap menunggu element yang dicari
    AddDataIeee(listDosen, options, waiting_time)
    AddDataDoaj(listDosen, options, waiting_time)
    AddRG(listDosen, options,waiting_time)
    AddDataSinta(listDosen, options)
    return redirect('../paper/')
