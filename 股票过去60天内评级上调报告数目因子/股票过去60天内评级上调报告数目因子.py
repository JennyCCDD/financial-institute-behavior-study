# -*- coding: utf-8 -*-
__author__ = "Mengxuan Chen"
__email__  = "chenmx19@mails.tsinghua.edu.cn"
__date__   = "20200703"

import numpy as np
import pandas as pd
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')
from getTradingDate import getTradingDateFromJY

class Para():
    startDate = 20060131
    endDate = 20200508
    lookBackDay = 60
    dataPathPrefix = 'D:\caitong_security'
    pass
para = Para()

# get time series
tradingDateList = getTradingDateFromJY(para.startDate, para.endDate, ifTrade=True, Period='D')
# get original data
StockReportTargetPriceAdjust = pd.read_hdf(para.dataPathPrefix +
'\DataBase\Data_AShareConsensusData\Data_EarningForecast\Data_ReportTargetPriceAdjust\Data\StockReportTargetPriceAdjust.h5')

'''1 未调
2 上调
3 下调
NULL 未知'''
# get stock codes
all_stock_list = StockReportTargetPriceAdjust.stock_code.unique()

predict_up_list_all = []
for k, stock_k in enumerate(tqdm(all_stock_list)):
    tmpDf = StockReportTargetPriceAdjust.loc[StockReportTargetPriceAdjust['stock_code'] == stock_k,:]
    up_list = []
    for i, curentDate in enumerate(tradingDateList):
        lastDate = tradingDateList[tradingDateList.index(curentDate) - para.lookBackDay]
        tmpDf2 = tmpDf[(tmpDf.current_create_date >= lastDate) & \
                      (tmpDf.current_create_date <= curentDate)]
        up = len(tmpDf2.loc[tmpDf2['price_adjust_mark'] == 2])
        up_list.append(up)
    predict_up_list_all.append(up_list)
predict_up = pd.DataFrame(predict_up_list_all, index=all_stock_list, columns=tradingDateList)
predict_up.to_csv('predict_up.csv')

