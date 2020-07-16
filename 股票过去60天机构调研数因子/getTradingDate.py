# -*- coding: utf-8 -*-
"""
Created on Thur Jun 27 11:08:11 2019

@author: 潘慧丽
@description:
    下载交易日表，以获取一段时间区间的交易日，日历日，每个月末的最后一个交易日，日历日
    所用到的表格：最新股本结构表QT_TradingDayNew
    此处是读取QT_TradingDayNew，再生成相应日期
@revise log:
    2019.10.16 如果endDate不在包含的列表里面，则将其添加进去
    2019.11.14 改写getTradingDate函数，默认用Wind接口提取，否则用聚源（主要为了防止聚源接口经常失效的情况）
    2020.4.13 getTradingDateOffset函数，修复currentDate不是交易日的问题
"""

# In[] import modules
import numpy as np
import pandas as pd
# from utils import conn
# from WindPy import w

# In[] 定义最终的函数，默认从wind中提取，否则从聚源中提取
def getTradingDate(startDate, endDate, ifTrade=True, Period='D'):
    """
    desciption:
        startDate:开始时间，int格式
        endDate:截止时间，int格式
        ifTrade: 是否为交易日，默认交易日，False为日历日
        Period: 日期频率，'D','W','M','Q','Y'
    """
    try:
        if(ifTrade==False):
            str1 = "Days=Alldays;"
        else:
            str1 = ""
        
        str2 = "Period="+Period
        options = str1+str2
            
        tmpData = w.tdays(str(startDate), str(endDate), options)
        w_tdays = [int(i.strftime('%Y%m%d')) for i in tmpData.Data[0]]        
    except:
        w_tdays = getTradingDateFromJY(startDate, endDate, ifTrade=ifTrade, Period=Period)
    return w_tdays




# In[] 定义用聚源提取数据的函数
def getTradingDateFromJY(startDate, endDate, ifTrade=True, Period='D'):
    """
    startDate：开始时间,int格式,如 20140101
    endDate:截止时间,格式同上
    if_trade：是否要交易日，默认交易日,取其他值为日历日
    Period: 日期频率'D','W','M','Q','Y')，默认'D'日度
    返回为list，其中日期是int格式
    """
    # 首先获取日期的表
    # 从数据库读取改为从本地读取##########################################################
    #sql = "select * from QT_TradingDayNew where SecuMarket in (83,90)"
    #df = pd.read_sql(sql, conn)


    df = pd.read_hdf('df.h5')

    #日期改成int格式
    df['TradingDate']  = df['TradingDate'].apply(lambda x:int(str(x)[:4] + str(x)[5:7] + str(x)[8:10]))
    df = df[(df.TradingDate>=int(startDate))&(df.TradingDate<=int(endDate))]

    #判断是否工作日，以及频度
    if ifTrade == True:
        df2 = df[df.IfTradingDay==1]
        if Period =='D':
            data = df2['TradingDate']
        elif Period =='W':
            data = df2[df2.IfWeekEnd==1]['TradingDate']
        elif Period == 'M':
            data = df2[df2.IfMonthEnd ==1]['TradingDate']
        elif Period == 'Q':
            data = df2[df2.IfQuarterEnd == 1]['TradingDate']
        elif Period =='Y':
            data = df2[df2.IfYearEnd ==1]['TradingDate']
        else:
            raise RuntimeError('Period必须为指定的格式：D, W, M, Q, Y等')
                
    else:
        data = pd.Series(pd.date_range(str(startDate),str(endDate),freq=Period[0])).apply(lambda x:int(str(x)[:4] + str(x)[5:7] + str(x)[8:10]))
    
    # revise date:2019.10.16
    # 如果endDate不在data里面，那么就将它添加进去，反之不处理    
    w_tdays = list(data)
    if(int(endDate) not in w_tdays):
        w_tdays.extend([int(endDate)])
        
    
    return w_tdays


# In[] 计算offset
def getTradingDateOffset(currentDate, offSetNum, ifTrade=True, Period='D'):
    """
    description:
        currentDate:当前日期
        offSetNum：前推或者后推的期数，往前推为负数，后推为正数
        Period:时间频率
    """
    # 读取时间
    # revise date:原来的写法只能往前推，不能往后推，现在我们要改写为可以往后推    
    #tradingDateList = getTradingDate(20000101, 20220202, ifTrade=ifTrade, Period=Period)
    # 减少数据量
    tradingDateList = getTradingDate(20200101, 20220202, ifTrade=ifTrade, Period=Period)
    currentDate = np.array(tradingDateList)[np.array(tradingDateList) >= currentDate][0]
    
    return tradingDateList[tradingDateList.index(currentDate) + offSetNum]




