# -*- coding: utf-8 -*-
__author__ = "Mengxuan Chen"
__email__  = "chenmx19@mails.tsinghua.edu.cn"
__date__   = "20200703"

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
# from WindPy import *
# w.start()
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class Para():
    startDate = 20091231
    endDate = 20200508
    weightMethod = '简单加权' # 简单加权 市值加权
    ret_calMethod = '简单' # 对数
    ret_style = '超额收益'  # 绝对收益 超额收益
    groupnum = 5
    normalize = 'None' # None Size Size_and_Industry
    factor = 'up'
    sample = 'in_sample' #in_sample  out_of_sample
    data_path = '.\\data\\'
    result_path = '.\\result\\'
    listnum = 121 # for stock sample at least be listed for listnum of days
    backtestwindow = 60 # number of days used to form portfolios
    fin_stock = 'yes' # include finnacial stock or not
    dataPathPrefix = 'D:\caitong_security'
    pass
para = Para()

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

class Industry():
    def __init__(self,para):
        # get trading date list as monthly frequancy
        self.tradingDateList = getTradingDateFromJY(para.startDate,
                                                    para.endDate,
                                                    ifTrade=True,
                                                    Period='M')

        self.Price, self.LimitStatus, self.Status, self.listDateNum, self.Industry, self.Size = basic_data(para)
        Factor = pd.read_csv(para.data_path + para.factor + '.csv', index_col=0)
        self.Factor = stock_dif(Factor, self.LimitStatus)
        self.df = pd.read_csv(para.data_path+'mean_industry_index.csv',index_col=0)


        pass

    def DES(self):
        Des = pd.DataFrame(self.Factor.describe())
        Des['all'] = Des.apply(lambda x: x.sum(), axis = 1)
        return Des['all']

    def every_month(self):
        # deal with the data every month
        meanlist = []
        corr_list = []
        for i,currentDate in enumerate(tqdm(self.tradingDateList[:-2])):
            lastDate = self.tradingDateList[self.tradingDateList.index(currentDate) - 1]
            nextDate = self.tradingDateList[self.tradingDateList.index(currentDate) + 1]
            if para.sample == 'in_sample':
                # use different method to calculate the return
                # logreturn for short time period and simple return calculation for long time period
                if para.ret_calMethod == '对数':
                    self.ret = np.log(self.Price.loc[currentDate, :] / self.Price.loc[lastDate, :])
                elif para.ret_calMethod == '简单':
                    self.ret = self.Price.loc[currentDate, :] / self.Price.loc[lastDate, :] - 1
                self.benchmark = pd.Series([self.df.iloc[i , 0]] * len(self.Factor.columns),
                                           index=self.ret.index.copy())

            elif para.sample == 'out_of_sample':
                if para.ret_calMethod == '对数':
                    self.ret = np.log(self.Price.loc[nextDate, :] / self.Price.loc[currentDate, :])
                elif para.ret_calMethod == '简单':
                    self.ret = self.Price.loc[nextDate, :] / self.Price.loc[currentDate, :] - 1

                self.benchmark = pd.Series([self.df.iloc[i + 1,0]] * len(self.Factor.columns),index = self.ret.index.copy())

            self.dataFrame = pd.concat([self.Factor.loc[currentDate,:],
                                   self.ret,
                                   self.benchmark,
                                   self.LimitStatus.loc[currentDate,:],
                                   self.Status.loc[currentDate,:],
                                   self.listDateNum.loc[currentDate,:],
                                   self.Industry.loc[currentDate,:],
                                   self.Size.loc[currentDate,:]],
                                   axis=1, sort=True)
            self.dataFrame = self.dataFrame.reset_index()
            self.dataFrame.columns = ['stockid',
                                 'factor',
                                 'RET',
                                 'Bechmark',
                                 'LimitStatus',
                                 'Status',
                                 'listDateNum',
                                 'Industry',
                                 'Size']


            if para.normalize == 'Size':
                # 市值中性化
                self.dataFrame['factor'] = orthogonalize(self.dataFrame['factor'],self.dataFrame['Size'])
            elif para.normalize == 'Size_and_Industry':
                # 市值中性化与行业中性化
                dummy_Industry = pd.get_dummies(self.dataFrame['Industry'],prefix = 'Industry')
                X = pd.concat([dummy_Industry,self.dataFrame['Size']],axis = 1, sort = False)
                self.dataFrame['factor'] = orthogonalize(self.dataFrame['factor'],X)
            elif para.normalize == 'None':
                pass
            self.dataFrame = self.dataFrame.dropna()
            # dataFrame = dataFrame.loc[dataFrame['factor'] != 0]
            self.dataFrame = self.dataFrame.loc[self.dataFrame['LimitStatus'] == 0]# 提取非涨跌停的正常交易的数据
            self.dataFrame = self.dataFrame.loc[self.dataFrame['Status'] == 1]# 提取非ST/ST*/退市的正常交易的数据
            self.dataFrame = self.dataFrame.loc[self.dataFrame['listDateNum'] >= para.listnum]# 提取上市天数超过listnum的股票
            if para.fin_stock == 'no': # 非银行金融代号41
                self.dataFrame = self.dataFrame.loc[self.dataFrame['Industry'] != 41]


            self.dataFrame['premium'] = self.dataFrame['RET'] - self.dataFrame['Bechmark']
            self.industry_factor =self.dataFrame.groupby(by='Industry', as_index=False)['factor'].mean()
            self.industry_factor.sort_values(by = 'factor', ascending = False, inplace= True) # 降序排列
            self.industry_list = self.industry_factor.Industry

            self.long_industry_list = list(self.industry_factor.Industry[:int(len(self.industry_list)/para.groupnum)])
            self.short_industry_list = list(self.industry_factor.Industry[-int(len(self.industry_list)/para.groupnum):])
            self.mean_dict_long = {}
            self.mean_dict_short ={}
            if para.ret_style == '超额收益':
                for ll in range(len(self.long_industry_list)):
                    self.mean_dict_long[ll] = self.dataFrame.loc[self.dataFrame['Industry']==self.long_industry_list[ll]]['premium'].mean()
                for zz in range(len(self.short_industry_list)):
                    self.mean_dict_short[zz] = self.dataFrame.loc[self.dataFrame['Industry']==self.short_industry_list[zz]]['premium'].mean()
            elif para.ret_style == '绝对收益':
                for ll in range(len(self.long_industry_list)):
                    self.mean_dict_long[ll] = \
                    self.dataFrame.loc[self.dataFrame['Industry'] == self.long_industry_list[ll]]['RET'].mean()
                for zz in range(len(self.short_industry_list)):
                    self.mean_dict_short[zz] = \
                    self.dataFrame.loc[self.dataFrame['Industry'] == self.short_industry_list[zz]]['RET'].mean()

            if para.weightMethod == '简单加权':
                meanlist.append(np.array(
                    self.mean_dict_long[0]
                    # + self.mean_dict_long[1]
                    # + self.mean_dict_long[2]
                    # + self.mean_dict_long[3]
                    # + self.mean_dict_long[4]

                    - self.mean_dict_short[0]
                    # - self.mean_dict_short[1]
                    # - self.mean_dict_short[2]
                    # - self.mean_dict_short[3]
                    # - self.mean_dict_short[4]

                    ))


            elif para.weightMethod == '市值加权':
                pass


        self.meanDf = pd.DataFrame(meanlist,index = self.tradingDateList[:-2])
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
            portfolioDF['ret'] = self.meanDf.iloc[1:,oneleg]
            portfolioDF['nav'] = (portfolioDF['ret']+1).cumprod()
            performance_df = performance(portfolioDF,para)
            performance_df_anl = performance_anl(portfolioDF,para)
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
        compare.index = self.meanDf.index[1:]
        plt.plot(range(len(compare)),
                 compare)
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
    main_fun = Industry(para)
    result = main_fun.every_month()
    print(result)
    result.to_csv(para.result_path + '_' + para.factor + '_' + para.weightMethod +
                  '_' + para.normalize + '_result.csv')
    test, test_nav = main_fun.portfolio_test()
    print(test)
    test.to_csv(para.result_path + '_' + para.factor + '_' + para.weightMethod +
                '_' + para.normalize + '_performance.csv')

# data = w.wsd(
#     "CI005001.WI,CI005002.WI,CI005003.WI,CI005004.WI,CI005005.WI,CI005006.WI,CI005007.WI,CI005008.WI,CI005009.WI,CI005010.WI,CI005011.WI,CI005012.WI,CI005013.WI,CI005014.WI,CI005015.WI,CI005016.WI,CI005017.WI,CI005018.WI,CI005019.WI,CI005020.WI,CI005021.WI,CI005022.WI,CI005023.WI,CI005024.WI,CI005025.WI,CI005026.WI,CI005027.WI,CI005028.WI,CI005029.WI,CI005030.WI",
#     "close",
#     "2009-12-31", "2020-05-08", "Period=D")
# self.df = pd.DataFrame(data.Data, index=data.Codes, columns=data.Times).T
# self.df.index = self.Factor.index.copy()
# self.df.fillna(0.0001) # CI005030.WI 2017年以后才有数据
# self.df.dropna(axis = 1,inplace = True)
# self.df['mean'] = self.df[:-1].apply(lambda x: x.mean(), axis = 0)
'''
0                 10              石油石化
1                 11                煤炭
2                 12              有色金属
3                 20           电力及公用事业
4                 21                钢铁
5                 22              基础化工
6                 23                建筑
7                 24                建材
8                 25              轻工制造
9                 26                机械
10                27          电力设备及新能源
11                28              国防军工
12                30                汽车
13                31              商贸零售
14                32             消费者服务
15                33                家电
16                34              纺织服装
17                35                医药
18                36              食品饮料
19                37              农林牧渔
20                40                银行
21                41             非银行金融
22                42               房地产
23                43              综合金融
24                50              交通运输
25                60                电子
26                61                通信
27                62               计算机
28                63                传媒
29                70                综合

'''
# dataFrame = dataFrame.sort_values(by='Industry', ascending=False)
# df_groupby = dataFrame.groupby(by='Industry', as_index=False).max()
# self.industry_factor = np.array(dataFrame.groupby('Industry')['factor'].mean())
# max_industry = np.argwhere(np.max(self.industry_factor.mean))
# self.mean_dict_long.sum() -self.mean_dict_short.sum()
# self.dataFrame.loc[self.dataFrame['Industry']==self.long_industry_list[0]]['premium'].mean() +
# self.dataFrame.loc[self.dataFrame['Industry']== self.long_industry_list[1]]['premium'].mean() -
# # self.dataFrame.loc[self.dataFrame['Industry'] == self.long_industry_list[2]]['premium'].mean() +
# # self.dataFrame.loc[self.dataFrame['Industry'] == self.long_industry_list[3]]['premium'].mean() +
# # self.dataFrame.loc[self.dataFrame['Industry'] == self.long_industry_list[4]]['premium'].mean() -
# self.dataFrame.loc[self.dataFrame['Industry'] == self.short_industry_list[0]]['premium'].mean() -
# self.dataFrame.loc[self.dataFrame['Industry'] == self.short_industry_list[1]]['premium'].mean()
# self.dataFrame.loc[self.dataFrame['Industry'] == self.short_industry_list[2]]['premium'].mean() -
# self.dataFrame.loc[self.dataFrame['Industry'] ==self.short_industry_list[3]]['premium'].mean() -
# self.dataFrame.loc[self.dataFrame['Industry'] ==self.short_industry_list[4]]['premium'].mean()

# self.dataFrame_long = self.dataFrame.loc[self.dataFrame['Industry'] ==
#                                          self.long_industry_list[0] or
#                                          self.long_industry_list[1] or
#                                          self.long_industry_list[2] or
#                                          self.long_industry_list[3] or
#                                          self.long_industry_list[4]]
# self.dataFrame_short = self.dataFrame.loc[self.dataFrame['Industry'] ==
#                                          self.short_industry_list[0] or
#                                          self.short_industry_list[1] or
#                                          self.short_industry_list[2] or
#                                          self.short_industry_list[3] or
#                                          self.short_industry_list[4] ]

# for iii in long_industry_list:
#     self.dataFrame_long = self.dataFrame.loc[self.dataFrame['Industry'] == iii]
# for jjj in short_industry_list:
#     self.dataFrame_short = self.dataFrame.loc[self.dataFrame['Industry'] == jjj]
# self.dataFrame_long = dataFrame.loc[dataFrame['Industry'] in long_industry_list]
# self.dataFrame_short = dataFrame.loc[dataFrame['Industry'] in short_industry_list]

# if para.weightMethod == '简单加权':
#     meanlist.append(np.array(self.dataFrame_long['premium'].mean()-self.dataFrame_short['premium'].mean()))
# elif para.weightMethod == '市值加权':
#     pass

# self.industry_factor = dataFrame.groupby(by='Industry', as_index=False)['factor'].mean().max()
# self.dataFrame2 = dataFrame.loc[dataFrame['Industry'] == self.industry_factor.Industry]
#
# self.dataFrame2['premium'] = self.dataFrame2['RET'] - self.dataFrame2['Bechmark']
# if para.weightMethod == '简单加权':
#     meanlist.append(np.array(self.dataFrame2['premium'].mean()))
# elif para.weightMethod == '市值加权':
#     pass
# meanlist.append(np.array((self.dataFrame2['RET'] * self.dataFrame2['Size']/self.dataFrame2['Size']).sum()))
# dataFrame['industry_factor_mean'] = dataFrame.groupby('Industry')['factor'].mean()
# 对单因子进行排序打分
#     dataFrame = dataFrame.sort_values(by = 'factor', ascending = False) # 降序排列
#     Des = dataFrame['factor'].describe()
#
#
#     dataFrame['Score'] = ''
#     eachgroup = int(Des['count']/ para.groupnum)
#     for groupi in range(0,para.groupnum-1):
#         dataFrame.iloc[groupi*eachgroup:(groupi+1)*eachgroup,-1] = groupi+1
#     dataFrame.iloc[(para.groupnum-1) * eachgroup:, -1] = para.groupnum
#
#     dataFrame['Score'].type = np.str
#     if para.weightMethod == '简单加权':
#         meanlist.append(np.array(dataFrame.groupby('Score')['RET'].mean()))
#     elif para.weightMethod == '市值加权':
#         meanlist_group = []
#         for groupi in range(0,para.groupnum):
#             dataFrame_ = dataFrame.iloc[groupi * eachgroup:(groupi + 1) * eachgroup, :]
#             meanlist_g = weightmeanFun(dataFrame_)
#             meanlist_group.append(meanlist_g)
#         meanlist.append(meanlist_group)
#