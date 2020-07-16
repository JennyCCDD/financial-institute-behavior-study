import pandas as pd
class Para():
    startDate = 20091231
    endDate = 20200508
    lookBackDay = 60
    dataPathPrefix = 'D:\caitong_security'
    pass
para = Para()
Data_AShareIndustryClass = pd.read_hdf(
    para.dataPathPrefix + '\DataBase\Data_AShareIndustryClass\AShareIndustriesClassCITICSNew_FirstIndustries.h5')
Data_AShareIndustryClass = Data_AShareIndustryClass.loc[para.startDate:para.endDate,:]
Data_industrycalss = pd.read_hdf((
    para.dataPathPrefix + '\DataBase\Data_AShareIndustryClass\CITICSNew_FirstIndustriesName.h5')
)

# from WindPy import *
# w.start()
# data = w.wsd("CI005001.WI,CI005002.WI,CI005003.WI,CI005004.WI,CI005005.WI,CI005006.WI,CI005007.WI,CI005008.WI,CI005009.WI,CI005010.WI,CI005011.WI,CI005012.WI,CI005013.WI,CI005014.WI,CI005015.WI,CI005016.WI,CI005017.WI,CI005018.WI,CI005019.WI,CI005020.WI,CI005021.WI,CI005022.WI,CI005023.WI,CI005024.WI,CI005025.WI,CI005026.WI,CI005027.WI,CI005028.WI,CI005029.WI,CI005030.WI", "close",
#              "2009-12-31", "2020-05-08", "Period=D")
# df =  pd.DataFrame(data.Data,index = data.Codes, columns = data.Times).T
# df.dropna(axis = 1,inplace = True)
# df['mean'] = df.apply(lambda x: x.sum(), axis = 0)
# df.index = Data_AShareIndustryClass.index.copy()

