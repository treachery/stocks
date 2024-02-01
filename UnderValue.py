import requests


# 现金流折现率估值法
def DCF(cash, grow_year, grow_rate, discount):
    cash_rate = 1 + ((grow_rate - discount) / 100)

    total_cash_rate = 0
    max_cash_rate_year = 0
    # 增长现金流
    for i in range(grow_year):
        total_cash_rate += cash_rate ** i
        max_cash_rate_year = cash_rate ** i

    # 永续现金流
    for i in range(20):  # 永续增长
        total_cash_rate += max_cash_rate_year * (1 - (discount / 100)) ** i

    return cash * total_cash_rate


# 投资回报率(按芒格说法，按PB=1买入一个公司，则投资回报率等于净资产收益率)
def ROIC(roic, pb, grow):
    return roic / pb * (1 + (grow / 100))

# 以DCF和ROIC筛选出优质且低估的企业
# 选股条件
# 市净率MRQ为0~10；
# 总市值为>100亿；
# 每股经营现金流为>1：
# 投入资本回报率ROIC为>10%；
# 净利率为20%~99%；
# 净利润3年复合增长率为>10%；
# 营收3年复合增长率为>10%；
# 预测净利润同比增长为>10%；
# 预测营收同比增长为>10%；
# 上市以来年化收益率为>10%

# (PBNEWMRQ>0)(PBNEWMRQ<=10)(TOTAL_MARKET_CAP>10000000000)(ROIC>10)(SALE_NPR>10)(NETPROFIT_GROWTHRATE_3Y>10)(INCOME_GROWTHRATE_3Y>10)(PREDICT_NETPROFIT_RATIO>10)(PREDICT_INCOME_RATIO>10)(PER_NETCASH_OPERATE>1)
# (PBNEWMRQ>0)(PBNEWMRQ<=10)(TOTAL_MARKET_CAP>1000000000)(ROIC>5)(SALE_NPR>10)(NETPROFIT_GROWTHRATE_3Y>0)(INCOME_GROWTHRATE_3Y>0)(PREDICT_NETPROFIT_RATIO>0)(PREDICT_INCOME_RATIO>0)(PER_NETCASH_OPERATE>1)
uri = "https://datacenter.eastmoney.com/stock/selection/api/data/get/"
d = {
    "type": "RPTA_SECURITY_STOCKSELECT",
    "sty": "ECURITY_CODE,SECURITY_NAME_ABBR,NEW_PRICE,PBNEWMRQ,ROIC,NETPROFIT_GROWTHRATE_3Y,INCOME_GROWTHRATE_3Y,PREDICT_NETPROFIT_RATIO,PREDICT_INCOME_RATIO,SALE_NPR,PER_NETCASH_OPERATE,TOTAL_MARKET_CAP",
    "filter": '(MARKET IN ("上交所主板","深交所主板","深交所创业板","上交所科创板","上交所风险警示板","深交所风险警示板","北京证券交易所"))(PBNEWMRQ>0)(PBNEWMRQ<=10)(TOTAL_MARKET_CAP>1000000000)(ROIC>5)(SALE_NPR>10)(NETPROFIT_GROWTHRATE_3Y>-5)(INCOME_GROWTHRATE_3Y>-5)(PREDICT_NETPROFIT_RATIO>0)(PREDICT_INCOME_RATIO>0)(PER_NETCASH_OPERATE>1)',
    "p": 1,
    "ps": 500,
    "sr": -1,
    "st": "TOTAL_MARKET_CAP",
    "source": "SELECT_SECURITIES",
    "client": "WEB",
}
r = requests.post(uri, data=d)
if r.status_code != 200:
    raise Exception("status_code: ", r.status_code)

data = r.json()["result"]["data"]

print(['NAME', 'NEW_PRICE', 'PB', 'ROIC', 'GROW', 'ROIC_RETURN', 'ROIC_PRICE', 'DCF_PRICE', 'SCORE'])
for i in r.json()["result"]["data"]:
    # ROIC
    # 非常非常保守的增长率估算: MIN(过去3年平均增长率的一半,分析师预估未来的增长率的1/3)
    GROWTHRATE = min(i['NETPROFIT_GROWTHRATE_3Y'] / 2, i['INCOME_GROWTHRATE_3Y'] / 2, i['PREDICT_NETPROFIT_RATIO'] / 3,
                     i['PREDICT_INCOME_RATIO'] / 3)
    ROIC_RETURN = ROIC(i['ROIC'], i['PBNEWMRQ'], GROWTHRATE)
    # 以长期投资回报率5%为分界, 计算合理估值
    ROIC_PRICE = ROIC_RETURN / 5 * i['NEW_PRICE']

    # DCF
    # 以 净利润/ROIC/当前规模 判断公司的增长潜力, 高利润率，市值1000亿以下企业认为增长更久
    CASH_PER = 1 + ((GROWTHRATE - 10) / 100)
    GROW_YEAR = 5  # 利润率低，增长5年
    if i['SALE_NPR'] > 50 and i['ROIC'] > 30 and i['TOTAL_MARKET_CAP'] < 100000000000:  # 利润率高，增长10年
        GROW_YEAR = 10

    CASH_PRICE = DCF(i['PER_NETCASH_OPERATE'] * 1.35, GROW_YEAR, GROWTHRATE, 10)
    SCORE = (CASH_PRICE / i['NEW_PRICE'] + ROIC_PRICE / i['NEW_PRICE']) / 2
    if SCORE > 0.9 and ROIC_RETURN > 3.5:
        print([i['SECURITY_NAME_ABBR'], i['NEW_PRICE'], i['PBNEWMRQ'], i['ROIC'], GROWTHRATE, ROIC_RETURN, ROIC_PRICE, CASH_PRICE, SCORE])
