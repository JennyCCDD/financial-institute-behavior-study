# -*- coding: utf-8 -*-
__author__ = "Mengxuan Chen"
__email__  = "chenmx19@mails.tsinghua.edu.cn"
__date__   = "20200601-20200622"

'''
新增市值中性化，行业和市值中性化
'''

import numpy as np
import pandas as pd
from tqdm import tqdm
from scipy.stats import spearmanr
from getTradingDate import getTradingDateFromJY
from utils import weightmeanFun, basic_data, stock_dif, performance, performance_anl
from datareader import loadData
import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def orthogonalize(regressY, regressX):
    # regressY: 因变量数据
    # regressX: 自变量数据

    # 首先给自变量因子加上截距项
    regressX = sm.add_constant(regressX)

    data = pd.concat([regressX, regressY], axis=1)
    data = data.dropna()

    # 我们不能直接用下面的这种形式，因为它丢失了标签栏的很多信息
    # est = sm.OLS(regressY, regressX, missing = 'drop').fit()

    # 注意,iloc这个是不包含
    est = sm.OLS(data.iloc[:, -1], data.iloc[:, 0:2]).fit()

    df = pd.Series(np.nan, regressX.index)
    df[data.index] = est.resid

    return df

class Para():
    startDate = 20091231
    endDate = 20200508
    groupnum = 10
    weightMethod = '市值加权' # 简单加权 市值加权
    ret_calMethod = '简单' # 对数
    normalize = 'Size' # None Size Size_and_Industry
    factor = 'up'
    sample = 'out_of_sample' #in_sample
    data_path = '.\\data\\'
    result_path = '.\\result\\'
    listnum = 121 # for stock sample at least be listed for listnum of days
    backtestwindow = 60 # number of days used to form portfolios
    fin_stock = 'no' # include finnacial stock or not
    dataPathPrefix = 'D:\caitong_security'
    pass
para = Para()

class SingleFactor():
    def __init__(self,para):
        # get trading date list as monthly frequancy
        self.tradingDateList = getTradingDateFromJY(para.startDate,
                                                    para.endDate,
                                                    ifTrade=True,
                                                    Period='M')

        self.Price, self.LimitStatus, self.Status, self.listDateNum, self.Industry, self.Size = basic_data(para)
        # self.Factor = pd.read_excel(para.data_path + para.factor + '.xlsx',index_col = 0).T
        Factor = pd.read_csv(para.data_path + para.factor + '.csv', index_col=0)
        self.Factor = stock_dif(Factor, self.LimitStatus)
        # self.Factor = Factor.loc[para.startDate:para.endDate, :]
        # self.Factor.index = self.LimitStatus.index.copy()
        # Factor.index.astype('str')
        # Factor.index = pd.to_datetime(Factor.index, format='%Y%m%d')


        # self.Price = stock_dif(self.Price,self.Factor)
        # self.LimitStatus = stock_dif(self.LimitStatus, self.Factor)
        # self.Status = stock_dif(self.Status, self.Factor)
        # self.listDateNum = stock_dif(self.listDateNum, self.Factor)
        # self.Industry = stock_dif(self.Industry, self.Factor)
        # self.Size = stock_dif(self.Size, self.Factor)

        # self.Factor.index = self.LimitStatus.index
        pass

    def DES(self):
        Des = pd.DataFrame(self.Factor.describe())
        Des['all'] = Des.apply(lambda x: x.sum(), axis = 1)
        return Des['all']

    def every_month(self):
        # deal with the data every month
        meanlist = []
        corr_list = []
        for i,currentDate in enumerate(tqdm(self.tradingDateList[:-1])):
            lastDate = self.tradingDateList[self.tradingDateList.index(currentDate) - 1]
            nextDate = self.tradingDateList[self.tradingDateList.index(currentDate) + 1]
            if para.sample == 'in_sample':
                # use different method to calculate the return
                # logreturn for short time period and simple return calculation for long time period
                if para.ret_calMethod == '对数':
                    self.ret = np.log(self.Price.loc[currentDate, :] / self.Price.loc[lastDate, :])
                elif para.ret_calMethod == '简单':
                    self.ret = self.Price.loc[currentDate, :] / self.Price.loc[lastDate, :] - 1
            elif para.sample == 'out_of_sample':
                if para.ret_calMethod == '对数':
                    self.ret = np.log(self.Price.loc[nextDate, :] / self.Price.loc[currentDate, :])
                elif para.ret_calMethod == '简单':
                    self.ret = self.Price.loc[nextDate, :] / self.Price.loc[currentDate, :] - 1
            dataFrame = pd.concat([self.Factor.loc[currentDate,:],
                                   self.ret,
                                   self.LimitStatus.loc[currentDate,:],
                                   self.Status.loc[currentDate,:],
                                   self.listDateNum.loc[currentDate,:],
                                   self.Industry.loc[currentDate,:],
                                   self.Size.loc[currentDate,:]],
                                   axis=1, sort=True)
            dataFrame = dataFrame.reset_index()
            dataFrame.columns = ['stockid',
                                 'factor',
                                 'RET',
                                 'LimitStatus',
                                 'Status',
                                 'listDateNum',
                                 'Industry',
                                 'Size']

            if para.normalize == 'Size':
                # 市值中性化
                dataFrame['factor'] = orthogonalize(dataFrame['factor'],dataFrame['Size'])
            elif para.normalize == 'Size_and_Industry':
                # 市值中性化与行业中性化
                dummy_Industry = pd.get_dummies(dataFrame['Industry'],prefix = 'Industry')
                X = pd.concat([dummy_Industry,dataFrame['Size']],axis = 1, sort = False)
                dataFrame['factor'] = orthogonalize(dataFrame['factor'],X)
            elif para.normalize == 'None':
                pass
            dataFrame = dataFrame.dropna()
            # dataFrame = dataFrame.loc[dataFrame['factor'] != 0]
            dataFrame = dataFrame.loc[dataFrame['LimitStatus'] == 0]# 提取非涨跌停的正常交易的数据
            dataFrame = dataFrame.loc[dataFrame['Status'] == 1]# 提取非ST/ST*/退市的正常交易的数据
            dataFrame = dataFrame.loc[dataFrame['listDateNum'] >= para.listnum]# 提取上市天数超过listnum的股票
            if para.fin_stock == 'no': # 非银行金融代号41
                dataFrame = dataFrame.loc[dataFrame['Industry'] != 41]

            # 对单因子进行排序打分
            dataFrame = dataFrame.sort_values(by = 'factor', ascending = False) # 降序排列
            Des = dataFrame['factor'].describe()

            ############################################ 计算spearman秩相关系数
            corr, t = spearmanr(
                dataFrame.loc[:, 'factor'],
                dataFrame.loc[:, 'RET'])
            corr_list.append(corr)


            dataFrame['Score'] = ''
            eachgroup = int(Des['count']/ para.groupnum)
            for groupi in range(0,para.groupnum-1):
                dataFrame.iloc[groupi*eachgroup:(groupi+1)*eachgroup,-1] = groupi+1
            dataFrame.iloc[(para.groupnum-1) * eachgroup:, -1] = para.groupnum

            dataFrame['Score'].type = np.str
            if para.weightMethod == '简单加权':
                meanlist.append(np.array(dataFrame.groupby('Score')['RET'].mean()))
            elif para.weightMethod == '市值加权':
                meanlist_group = []
                for groupi in range(0,para.groupnum):
                    dataFrame_ = dataFrame.iloc[groupi * eachgroup:(groupi + 1) * eachgroup, :]
                    meanlist_g = weightmeanFun(dataFrame_)
                    meanlist_group.append(meanlist_g)
                meanlist.append(meanlist_group)

        self.meanDf = pd.DataFrame(meanlist,index = self.tradingDateList[:-1])
        self.corr_avg = np.mean(corr_list)
        print('RankIC', round(self.corr_avg, 6))
        return self.meanDf

    def portfolio_test(self):
        sharp_list = []
        ret_list = []
        std_list = []
        mdd_list = []
        r2var_list = []
        cr2var_list = []
        compare= pd.DataFrame()
        for oneleg in tqdm(range(len(self.meanDf.columns))):
            portfolioDF = pd.DataFrame()
            portfolioDF['ret'] = self.meanDf.iloc[:,oneleg]
            portfolioDF['nav'] = (portfolioDF['ret']+1).cumprod()
            performance_df = performance(portfolioDF,para)
            # performance_df_anl = performance_anl(portfolioDF,para)
            sharp_list.append(np.array(performance_df.iloc[:,0].T)[0])
            ret_list.append(np.array(performance_df.iloc[:,1].T)[0])
            std_list.append(np.array(performance_df.iloc[:,2].T)[0])
            mdd_list.append(np.array(performance_df.iloc[:,3].T)[0])
            r2var_list.append(np.array(performance_df.iloc[:,4].T)[0])
            cr2var_list.append(np.array(performance_df.iloc[:,5].T)[0])
            compare[str(oneleg)] = portfolioDF['nav']
        performanceDf = pd.concat([pd.Series(sharp_list),
                                   pd.Series(ret_list),
                                   pd.Series(std_list),
                                   pd.Series(mdd_list),
                                   pd.Series(r2var_list),
                                   pd.Series(cr2var_list)],
                                    axis = 1, sort = True)
        performanceDf.columns = ['Sharp',
                                 'RetYearly',
                                 'STD',
                                 'MDD',
                                 'R2VaR',
                                 'R2CVaR']
        compare.index = self.meanDf.index
        plt.plot(range(len(compare.iloc[1:, 1])),
                 compare.iloc[1:, :])
        plt.title(para.factor)
        plt.xticks([0, 25, 50, 75, 100, 125],
                   ['2009/12/31', '2011/01/31', '2013/02/28', '2015/03/31', '2017/04/30', '2020/04/30'])
        plt.grid(True)
        plt.xlim((0, 125))
        plt.legend()
        plt.savefig(para.result_path + para.factor +'_'+para.weightMethod+
                '_'+para.normalize+'_performance_nav.png')
        plt.show()
        return performanceDf,compare

if __name__ == "__main__":
    para = Para()
    main_fun = SingleFactor(para)
    des = main_fun.DES()
    result = main_fun.every_month()
    print(result)
    result.to_csv(para.result_path+'_' + para.factor +'_'+para.weightMethod+
                '_'+para.normalize+'_result.csv')
    test, test_nav = main_fun.portfolio_test()
    print(test)
    test.to_csv(para.result_path +'_'+ para.factor +'_'+para.weightMethod+
                '_'+para.normalize+'_performance.csv')