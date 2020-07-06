# -*- coding: utf-8 -*-
__author__ = "Mengxuan Chen"
__email__  = "chenmx19@mails.tsinghua.edu.cn"
__date__   = "20200605"

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
StockReportForecast = pd.read_hdf(para.dataPathPrefix +
'\DataBase\Data_AShareConsensusData\Data_EarningForecast\Data_ReportForecastStock\Data\StockReportForecast.h5')
# get stock codes
all_stock_list = StockReportForecast.stock_code.unique()

# calculate coverage in backtest number of days for each stock
cov_list_all = []
for k, stock_k in enumerate(tqdm(all_stock_list)):
    tmpDf = StockReportForecast.loc[StockReportForecast['stock_code'] == stock_k,:]
    # just consider the main author
    tmpDf['author_main'] = tmpDf['author_name'].apply(lambda x: str(x)[:3]).tolist()
    cov_list = []
    for i, curentDate in enumerate(tradingDateList):
        lastDate = tradingDateList[tradingDateList.index(curentDate) - para.lookBackDay]
        tmpDf2 = tmpDf[(tmpDf.create_date >= lastDate) & \
                      (tmpDf.create_date <= curentDate)]
        coverage = len(tmpDf2)
        cov_list.append(coverage)
    cov_list_all.append(cov_list)
cov = pd.DataFrame(cov_list_all,index = all_stock_list, columns = tradingDateList)
cov.to_csv('coverage.csv')






# 计算每个分析师覆盖的股票的数量
# all_author_list = StockReportForecast.author_name.unique()
# all_stock_list = StockReportForecast.stock_code.unique()
# df = pd.DataFrame(index = tradingDateList, columns = all_author_list)
# for i, curentDate in enumerate(tqdm(tradingDateList)):
#     lastDate = tradingDateList[tradingDateList.index(curentDate) - para.lookBackDay]
#     tmpDf = StockReportForecast[(StockReportForecast.create_date>= lastDate)&\
#                                 (StockReportForecast.create_date<= curentDate)]
#     if len(tmpDf.index) == 0:
#         pass
#     else:
#         print(tmpDf.groupby('author_name')['create_date'].value_counts())

# 计算每个个股被几个分析师所覆盖
# everyday_list=[]
# # coverageDf = pd.DataFrame()
# coverage_list = []
# for i, curentDate in enumerate(tqdm(tradingDateList)):
#     lastDate = tradingDateList[tradingDateList.index(curentDate) - para.lookBackDay]
#     tmpDf = StockReportForecast[(StockReportForecast.create_date >= lastDate) & \
#                                 (StockReportForecast.create_date <= curentDate)]
#     tmpDf['author_main'] = tmpDf['author_name'].apply(lambda x: str(x)[:3]).tolist()
#     if len(tmpDf.index) == 0:
#         coverage_list.append(0)
#         pass
#     else:
#         tmpDf2 = tmpDf.groupby('stock_code')['author_main'].apply(lambda x: len(x.index))
#         coverage_list.append(np.array(tmpDf2.T))

# coverageDf = pd.DataFrame(coverage_list)
# tmpDf2.columns = ['stockid','coverage']
# tmpDf2.set_index(['stockid'], inplace=True)
# coverageDf.iloc[i,:] = tmpDf2
# def countdef(df):
#     dff = len(df.index)
#     return dff
# print(tmpDf.groupby('stock_code')['author_main'].describe().T.unstack())
#     everystock_list = []
#     if len(tmpDf.index) == 0:
#         everystock_list.append(0)
#     else:
#         for stockj in all_stock_list:
#             tmpDf2 = tmpDf[(tmpDf.stock_code == stockj)]
#             tmpDf2['author_main'] = tmpDf2['author_name'].apply(lambda x:str(x)[:3]).tolist()
#             everystock_list.append(len(tmpDf2['author_name'].unique()))
#     everyday_list.append(everystock_list)
# print(everyday_list)

