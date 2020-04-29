import os
import requests
import time

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import openpyxl

from nsQtUtil import *
from PyQt5.QtWidgets import *

from CrawlData import CrawlData

# 네이버 쇼핑
URL_NAVER_SHOP = "https://shopping.naver.com/"

# 저장 폴더
FOLDER_PATH = "SHOP CRAWLER"

# 모든 카테고리 정보
bigCategoryTextList = []
categoryTextList = [[]]
categoryLinkList = [[]]

# 크롤링한 데이터
crawlDataList = [[[] for first in range(100)] for second in range(50)]

# webDriver . Chrome driver Ver.80
driver = webdriver.Chrome("chromedriver.exe")

# 카테고리 정보들 가져오기
def GetAllCategoryLink():
    driver.get(URL_NAVER_SHOP)
    time.sleep(1)
    
    # 카테고리 리스트 요소
    div_elems = driver.find_elements_by_xpath("//ul[@class='co_category_list']/li[@*]/a[@href='#']")
    
    CrawlBigCategory(driver.page_source)

    categoryIndex = 0
    for element in div_elems:
        element.send_keys(Keys.ENTER)
        CrawlAllCategory(driver.page_source, categoryIndex)
        categoryIndex += 1

def CrawlBigCategory(html):    
    bsObj = BeautifulSoup(html, "html.parser")    
    itemList = bsObj.find_all('ul', {"class" :"co_category_list"})
    
    if bsObj == None:
        print("ERROR : URL FAULT [000] (url : ", url, ")")
        return

    for link in itemList[1].find_all('a'):
        if hasattr(link, 'attrs') and 'href' in link.attrs:
            bBigCategoryCheck  = "#" in link.attrs['href']
            if bBigCategoryCheck == True:
                bigCategoryTextList.append(link.text.strip())
                continue

def CrawlAllCategory(html, categoryIndex):
    bsObj = BeautifulSoup(html, "html.parser")    
    itemList = bsObj.find_all('ul', {"class" :"co_category_list"})
    
    if bsObj == None:
        print("ERROR : URL FAULT [001] (url : ", url, ")")
        return

    categoryTextList.append([])
    categoryLinkList.append([])

    #?? 왜 1만 되나
    for link in itemList[1].find_all('div', {"class" : "co_position"}):            
        for httpLink in link.find_all('a'):
            if hasattr(httpLink, 'attrs') and 'href' in httpLink.attrs:
                bHttpCheck = "http" in httpLink.attrs['href']
                if bHttpCheck == True:
                    categoryTextList[categoryIndex].append(httpLink.text.strip())
                    categoryLinkList[categoryIndex].append(httpLink.attrs['href'].strip())
                    continue
            
# 링크 없을때!!!! 예외처리하자
def ClickTab(xpath):
    time.sleep(1)

    if xpath == None:
        print("ERROR XPATH NULL [007]")
        return
    
    if driver.find_element_by_xpath(xpath) == None:
        print("ERROR element NULL [008]")
        return

    element = driver.find_element_by_xpath(xpath) #??이거 없을떄 예외 처리하자
    
    element.send_keys(Keys.ENTER)

# 모든 아이템의 정보 가져오기
def CrawlItemInfo(url, pageCount, listIndex0, listIndex1):
    driver.get(url)

    # 가격 비교 탭 + 페이지 탭 클릭
    #?? 페이지가 정해진 개수보다 작을때 예외처리해야됨 페이지 개수 갖고오자...
    ClickTab("//ul[@class='snb_list']/li[@class='snb_compare']/a[@href='#']")
    ClickTab("//div[@class='co_paginate']/a[@href='#']")

    # 기본 페이지 Index 설정 (1페이지로)
    tabLink = driver.current_url
    tabLink = tabLink.replace("2", "1", 1)    
    
    # 1페이지 정보 가져오기
    rqResult = requests.get(tabLink)
    bsObj = BeautifulSoup(rqResult.content, "html.parser")
    
    if bsObj == None:
        print("ERROR : URL FAULT [002] (url : ", url, ")")
        return

    # 크롤링 데이터 생성
    crawlData = CrawlData()

    # 요청한 페이지만큼 크롤링
    for pageNumber in range(1, pageCount + 1):
        itemList = bsObj.find('ul', {"class" : "goods_list"})

        if itemList == None:#?? 왜 가끔 폴트뜨지?
            print("ERROR : URL FAULT [003] (url : ", url, ")")
            break


        contentIndex = -1
        for content in itemList.contents:
            if hasattr(content, 'attrs') and 'class' in content.attrs:
                # 광고 거르기
                bAdCheck = 'ad' in content.attrs['class']
                if bAdCheck == False:
                    # INFO
                    itemInfo = content.find('div', {"class" : "info"})
                    itemTitle = itemInfo.find('div', {"class" : "tit"})
                    itemTitle = itemTitle.find('a', {"class" : "link"})
                    itemPrice = itemInfo.find('span', {"class" : "price"})
                    itemEtc = itemInfo.find('span', {"class" : "etc"})                
                    
                    # ETC
                    itemDate = itemEtc.find('span', {"class" : "date"})          

                    crawlData.itemDataList.append([])
                    
                    contentIndex += 1
                    crawlData.itemDataList[contentIndex].append(itemTitle.text.strip())
                    crawlData.itemDataList[contentIndex].append((itemPrice.text[0:itemPrice.text.find("원") + 1]).strip())
                    crawlData.itemDataList[contentIndex].append((itemPrice.text[itemPrice.text.find("원") + 1:]).strip())
                    crawlData.itemDataList[contentIndex].append(itemDate.text.strip())

                    crawlData.itemDataList[contentIndex].append("/--/")

                    # 판매처가 여러개 있을 경우 판매처 정보 크롤링
                    for itemPriceContent in itemPrice.contents:
                        if hasattr(itemPriceContent, 'attrs'):
                            bPriceCheck = 'href' in itemPriceContent.attrs
                            if bPriceCheck == True:
                                itemSellLink = itemPriceContent.attrs['href'].strip()
                                CrawlDetailItemInfo(itemSellLink, crawlData, contentIndex)
        
        # 다음 페이지로 이동
        tabLink = tabLink.replace(str(pageNumber), str(pageNumber + 1), 1)
        rqResult = requests.get(tabLink)
        bsObj = BeautifulSoup(rqResult.content, "html.parser")

    print(listIndex0, " " ,listIndex1, "크롤링 데이터 추가")
    crawlDataList[listIndex0][listIndex1].append(crawlData)
               
# 여러 판매처의 아이템 정보 가져오기
def CrawlDetailItemInfo(url, crawlData, contentIndex):    
    rqResult = requests.get(url)
    bsObj = BeautifulSoup(rqResult.content, "html.parser")
    
    tableList = bsObj.find('table', {"class" : "tbl_lst"})

    if tableList == None:
        return False #?? 원인 알아야함 아예 tbl list가 안 가져와지는 경우 많음

    itemList = tableList.find_all('tr', {"class" : "_itemSection"})
    
    for item in itemList:
        if hasattr(item, 'attrs') and 'class' in item.attrs:
            # PRICE
            price = item.find('td', {"class" : "price"})
            crawlData.itemDataList[contentIndex].append(price.text.strip())

            mall = item.find('span', {"class" : "mall"})
            if hasattr(mall.contents[0], 'attrs'):
                bCheck = 'href' in mall.contents[0].attrs
                if bCheck == True:
                    itemSellLink = mall.contents[0].attrs['href'].strip()
                    crawlData.itemDataList[contentIndex].append(itemSellLink)
                    
                else:
                    crawlData.itemDataList[contentIndex].append("")
            else:
                    crawlData.itemDataList[contentIndex].append("")

            # GIFT
            gift = item.find('td', {"class" : "gift"})
            if gift != None:
                crawlData.itemDataList[contentIndex].append(gift.text.strip())
            else:                
                crawlData.itemDataList[contentIndex].append("")  


            # INFO
            info = item.find('td', {"class" : "info"})
            if info != None:
                crawlData.itemDataList[contentIndex].append(info.text.strip())
            else:
                crawlData.itemDataList[contentIndex].append("")

            
            crawlData.itemDataList[contentIndex].append("/--/")
    return True

##
##
##
# 폴더가 없으면 생성한다
def CheckAndCreateFolder(folderPath):
    try:
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
    except OSError:
        print ("Error: Creating folder [004]: " + folderPath)

# 액셀 저장
def SaveItemListAsExcel(fileName):
    workBook = openpyxl.Workbook()

    excelSheet = []
    
    excelSheetIndex = 0

    for index0 in range(0, len(crawlDataList)):
        for index1 in range(0, len(crawlDataList[index0])):
            textIndex2 = 0
            for index2 in range(0, len(crawlDataList[index0][index1])):
                newSheet = workBook.create_sheet(categoryTextList[index0][textIndex2])
                textIndex2 += 1

                excelSheet.append(newSheet)
                excelSheet[excelSheetIndex].append(["제품 이름", "제품 가격", "판매처", "제품 등록일"])

                for index3 in range(0, len(crawlDataList[index0][index1][index2].itemDataList)):
                    excelSheet[excelSheetIndex].append(crawlDataList[index0][index1][index2].itemDataList[index3])

                excelSheet[excelSheetIndex].append([""])
                excelSheetIndex += 1

    CheckAndCreateFolder(FOLDER_PATH)

    workBook.save(FOLDER_PATH + "/" + fileName + ".xlsx")

    print("저장 완료")


# pageCount : 몇 페이지까지 크롤링 할 것인지
# boolList  : GUI에서 체크한 정보들만 boolList[index0][index1] = True
def StartCrawling(pageCount, boolList):
    if pageCount == None:
        pageCount = 1
        print("NO PAGE COUNT [005]")

    if boolList == None:
        boolList = [True for b in range(100)]
        print("NO BOOL LIST [006]")
        
    # 각 링크에서 데이터 크롤링
    #?? GUI에서 선택한 정보만 걸러서 가져와야한다.
    for index0 in range(0, len(boolList)):
        if boolList[index0] == False:
            continue
        for index1 in range(0,1):#len(categoryLinkList[index0])):
            CrawlItemInfo(categoryLinkList[index0][index1], pageCount, index0, index1)

        print(index0, "에서 60초 대기")
        time.sleep(60)

    SaveItemListAsExcel("네이버 쇼핑 데이터")

##
##
##
def OpenWindow(window):
    screenWidth = 900
    screenHeight = 480

    # Window 크기 및 위치 설정
    myDesktop = QApplication.desktop()
    rect = myDesktop.screenGeometry()
    window.setGeometry(rect.width() / 2 - screenWidth / 2, rect.height() / 2 - screenHeight / 2, screenWidth, screenHeight)
    
    window.InitializeWindow(bigCategoryTextList, StartCrawling)
    
##
##
##
def app_init(window):
    window.setWindowTitle("Naver Shopping Crawler (ver.1.0)")
    
    ##
    # 카테고리 링크 가져오기
    GetAllCategoryLink()
      
    ##
    # 윈도우 설정
    maxIndex1Count = 0
    for i in range(0, len(categoryLinkList)):
        if maxIndex1Count > len(categoryLinkList[i]):
            maxIndex1Count = len(categoryLinkList[i])

    maxIndex1Count += 1

    OpenWindow(window)
    
    ##
    ##
    #StartCrawling(None, boolList, len(categoryLinkList) + 1, maxIndex1Count)

    ##?? 파일명 GUI에서
    #SaveItemListAsExcel("네이버 쇼핑 데이터")


def main():    
    ##GUI CODE
    app = QApplication(sys.argv)
    window = MainWindow()
    app_init(window)
    
    widget = window.centralWidget()

    window.show()
    app.exec_()

##
##
##
#MAIN
main()