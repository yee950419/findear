from django.db import models

import pandas as pd
import numpy as np
import fasttext
from sklearn.preprocessing import MinMaxScaler
import haversine.haversine as hv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from kiwipiepy import Kiwi
import re
from dotenv import load_dotenv
import os
import time
import logging

from selenium import webdriver 
from selenium.webdriver.common.by import By # find_element 함수 쉽게 쓰기 위함
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import random
# Create your models here.

logger = logging.getLogger(__name__)
class matchModel():
    
    def logging_time(original_fn):
        def wrapper_fn(*args, **kwargs):
            start_time = time.time()
            result = original_fn(*args, **kwargs)
            end_time = time.time()
            print("WorkingTime[{}]: {} sec".format(original_fn.__name__, end_time-start_time))
            return result
        return wrapper_fn
    def __init__(self) -> None:
        # load model
        load_dotenv()
        path = os.getenv("MODEL_PATH")
        self.model = fasttext.load_model(path)

        self.kiwi = Kiwi()
        self.stem_tag = ['NNG', 'NNP', 'VA'] 
        # open color crawling
        self.webPath = 'http://web.kats.go.kr/KoreaColor/color.asp'
        self.driver = webdriver.Chrome()
        self.driver.get(self.webPath)
        print('driver', self.driver)
        self.timeToWait = 0.00001

        return None

    def setData(self, lost, found):
        self.lost = lost
        self.found = found
        logger.debug(f'Get Data')
        logger.debug(f'lost :: {lost}')
        logger.debug(f'found :: {found}')

    def preprocess(self, source):
        if source not in ['lost112', 'findear']: 
            raise Exception('input wrong')
        self.source = source 
        # set lost item type
        self.lost['lostBoardId'] = int(self.lost['lostBoardId'])
        self.lost['xpos'] = float(self.lost['xpos'])
        self.lost['ypos'] = float(self.lost['ypos'])

        # set found item type
        self.found = pd.DataFrame(self.found)
        self.found['acquiredBoardId'] = self.found['acquiredBoardId'].astype(int)

        if self.source == 'findear':
            self.found['xpos'] = self.found['xpos'].astype(float)
            self.found['ypos'] = self.found['ypos'].astype(float)
        elif self.source == 'lost112':
            pass

        self.score = pd.DataFrame()
        self.score['id'] = self.found['acquiredBoardId']

    def calColor(self):
        std = 100 
        self.score['color'] = 0
        lostColor = self.getColor(self.lost['color'])
        if lostColor is None: return None
        npLst = np.array([])
        for i in self.found['color']:
            foundColor = self.getColor(i)
            if foundColor is None:
                npLst = np.append(npLst,[255])
                continue
            diff = self.delta_E_CMC(lostColor, foundColor)
            npLst = np.append(npLst,[diff])
        #print('complete np', npLst )
        npLst = npLst.reshape(-1,1)
        minmaxScaler = MinMaxScaler().fit([[0],[std]])
        X_train_minmax = minmaxScaler.transform(npLst)
        nplst = 1 - np.array(X_train_minmax).squeeze()

        self.score['color'] = nplst
        return
    
    def calDistance(self):
        std = 20
        npLst = np.array([[hv((y,x), ( self.lost['ypos'],self.lost['xpos']), unit='km')] for x,y in zip(self.found['xpos'], self.found['ypos']) ])
        minmaxScaler = MinMaxScaler().fit([[0],[std]])
        X_train_minmax = minmaxScaler.transform(npLst)
        nplst = 1- np.array(X_train_minmax).squeeze()
        self.score['place'] = nplst
        return None
    
    def calName(self):
        lostName = self.lost['productName'].replace(' ','')
        foundName = self.found['productName'].map(lambda x: x.replace(' ', '')).to_list()
        npLst = np.array([self.getCoSim(self.model[lostName], self.model[i]) for i in foundName])
        self.score['name'] = npLst
        return None
    
    def calDesc(self):
        foundToken = [self.getDocumentToken(document) for document in self.found['description']]
        print(foundToken)
        lostToken = self.getDocumentToken(self.lost['description']) 

        lostVector = self.getDocumentVector(lostToken)
        foundVector = [self.getDocumentVector(document) for document in foundToken]

        npLst = np.array([self.getCoSim(lostVector, i) for i in foundVector])
        self.score['desc'] = npLst
    
    def aggregateScore(self):

        self.score['mean_value'] = self.score.iloc[:, 1:].mean(axis=1)
        self.score['mean_value'] = self.score['mean_value'].round(decimals=5)
        
        # 평균 값을 기준으로 DataFrame 정렬
        df_sorted = self.score.sort_values(by='mean_value', ascending=False)
        print(df_sorted)
        
        # 데이터프레임 순회하며 반환 형태로 변환하는 리스트 컴프리헨션
        lostBoardId = self.lost["lostBoardId"]
        result_data = [
            {"lostBoardId": int(lostBoardId), "acquiredBoardId": int(row["id"]), "similarityRate": row["mean_value"]}
            for index, row in df_sorted.loc[:, ['id', 'mean_value']].iterrows()
        ]
        
        print(result_data)
        return result_data  


    def test(self):
        print('teststest')
        return 'test'

    def getDocumentVector(self, document):
        vector = np.array(sum(self.model[doc] for doc in document)) / len(document)
        return vector

    def getDocumentToken(self, document):
        charEngNum = re.findall(r'[A-Za-z0-9]+', document)
        meaningfulText = self.kiwi.tokenize(document)
        token = [t.form for t in meaningfulText if t.tag in self.stem_tag] + charEngNum
        return token

    @logging_time
    def getColor(self, query):
        '''
        None 반환 시 색 계산 제외
        '''
        if query == '':
            return None
        elif len(query) == 1:
            query = query+'색' 
        inputBox = self.driver.find_element(By.XPATH,'/html/body/form/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/td[1]/table/tbody/tr/td[3]/table/tbody/tr[3]/td/table/tbody/tr/td[2]/input' )
        inputBox.clear()
        inputBox.send_keys(query)
        inputBox.send_keys(Keys.RETURN)
        self.driver.implicitly_wait(self.timeToWait)

        colorBox = self.driver.find_element(By.XPATH, '/html/body/form/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/td[1]/table/tbody/tr/td[3]/table/tbody/tr[6]/td/div/select')
        colorLst = colorBox.text.split('\n')
        if len(colorLst) == 1:
            index = 0
        elif len(colorLst) == 0:
            return None
        elif query in colorLst:
            index = colorLst.index(query)
        else:
            index = random.randint(0, len(colorLst))

        select = Select(colorBox)
        select.select_by_index(index)
        selected_option = select.first_selected_option
        action = ActionChains(self.driver)
        action.double_click(selected_option).perform()
        self.driver.implicitly_wait(self.timeToWait)

        #rgb = self.driver.find_element(By.NAME, 'html_text').get_attribute('value')
        labBox = self.driver.find_element(By.XPATH, '/html/body/form/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[3]/td[3]/table/tbody/tr[15]/td/table/tbody/tr')
        lab = labBox.find_elements(By.TAG_NAME, 'input')
        labLst = [float(i.get_attribute('value')) for i in lab]
        return labLst
    
    def getCodeFromColor(self, color):
        rgb = [int(color[i:i+1], base=16) for i in range(0,6,2)]
        return rgb

    def delta_E_CMC(self, Lab1, Lab2, l=2, c=1):
        '''
        Referenced from 
        https://www.colour-science.org/api/0.3.3/html/_modules/colour/difference/delta_e.html
        '''
        L1, a1, b1 = Lab1
        L2, a2, b2 = Lab2

        c1 = np.sqrt(a1 * a1 + b1 * b1)
        c2 = np.sqrt(a2 * a2 + b2 * b2)
        sl = 0.511 if L1 < 16 else (0.040975 * L1) / (1 + 0.01765 * L1)
        sc = 0.0638 * c1 / (1 + 0.0131 * c1) + 0.638
        h1 = 0 if c1 < 0.000001 else (np.arctan2(b1, a1) * 180) / np.pi

        while h1 < 0:
            h1 += 360

        while h1 >= 360:
            h1 -= 360

        t = (0.56 + np.fabs(0.2 * np.cos((np.pi * (h1 + 168)) / 180))
            if 164 <= h1 <= 345 else
            0.36 + np.fabs(0.4 * np.cos((np.pi * (h1 + 35)) / 180)))
        c4 = c1 * c1 * c1 * c1
        f = np.sqrt(c4 / (c4 + 1900))
        sh = sc * (f * t + 1 - f)

        delta_L = L1 - L2
        delta_C = c1 - c2
        delta_A = a1 - a2
        delta_B = b1 - b2
        delta_H2 = delta_A * delta_A + delta_B * delta_B - delta_C * delta_C

        v1 = delta_L / (l * sl)
        v2 = delta_C / (c * sc)
        v3 = sh

        return np.sqrt(v1 * v1 + v2 * v2 + (delta_H2 / (v3 * v3)))
    
    def getCoSim(self, word1, word2):
        return np.dot(word1, word2) / (np.linalg.norm(word1) * np.linalg.norm(word2))
    


if __name__ == '__main__':
    testLost = {
            "lostBoardId" : 1,
            "productName" : "어린이 카드지갑",
            "color" : "검정",
            "categoryName" : "지갑",
            "description" : "물품에 대한 설명",
            "aiDescription": "",
            "lostAt" : "2024-03-26 00:00:00",
            "xpos" :127.04,
            "ypos" : 37.5013
        }
    testFound = [
            {
                "acquiredBoardId" : 1,
                "productName" : "여성 장지갑",
                "color" : "하양",
                "categoryName" : "지갑",
                "description" : "왼쪽 상단에 흠집이 가있습니다.",
                "xpos" : 126.933,
                "ypos" : 37.545,
                "registeredAt" : "2024-03-25 00:00:00"
            },
            {
                "acquiredBoardId" : 2,
                "productName" : "에르메스",
                "color" : "파랑",
                "categoryName" : "지갑",
                "description" : "모델은 미상입니다. 한정판으로 보입니다.",
                "xpos" : 127.05,
                "ypos" : 37.5034,
                "registeredAt" : "2024-03-25 00:00:00"
            },
            {
                "acquiredBoardId" : 3,
                "productName" : "코끼리 그림 박힌 지갑",
                "color" : "초록",
                "categoryName" : "지갑",
                "description" :     "물품에 대한 설명",
                "xpos" : 126.23,
                "ypos" : 35.24,
                "registeredAt" : "2024-03-25 00:00:00"
            }
        ]
    testModel = matchModel()
    testModel.setData(testLost, testFound)
    
    testModel.preprocess('findear')
    testModel.calColor()
    testModel.calDistance()
    testModel.calName()
    testModel.calDesc()
    print(testModel.score)
    ans = testModel.aggregateScore()
    print(ans)