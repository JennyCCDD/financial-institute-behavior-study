# -*- coding: utf-8 -*-
__author__ = "Mengxuan Chen"
__email__  = "chenmx19@mails.tsinghua.edu.cn"
__date__   = "20200716"

import numpy as np
import pandas as pd
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')
from getTradingDate import getTradingDateFromJY

class Para():
    startDate = 20120131
    endDate = 20200508
    lookBackDay = 60
    dataPathPrefix = 'D:\caitong_security'
    pass
para = Para()

# get time series
tradingDateList = getTradingDateFromJY(para.startDate, para.endDate, ifTrade=True, Period='D')
# get original data
StockResearch = pd.read_hdf(para.dataPathPrefix +'\Data(1)\Data_StockInvestorRelation\Stock_InvestorRelationship.h5')

# get stock codes
all_stock_list = StockResearch.SecuCode.unique()
# In[]
stock_research_number = []
for k, stock_k in enumerate(tqdm(all_stock_list)):
    tmpDf = StockResearch.loc[StockResearch['SecuCode'] == stock_k,:]
    reseach_list = []
    for i, curentDate in enumerate(tradingDateList):
        lastDate = tradingDateList[tradingDateList.index(curentDate) - para.lookBackDay]
        tmpDf2 = tmpDf[(tmpDf.InfoPublDate >= lastDate) & \
                      (tmpDf.InfoPublDate <= curentDate)]
        research = len(tmpDf2)
        reseach_list.append(research)
    stock_research_number.append(reseach_list)
stock_research = pd.DataFrame(stock_research_number, index=all_stock_list, columns=tradingDateList)
stock_research.to_csv('stock_research.csv')

