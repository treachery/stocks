import requests

# 现金流折现率估值法
def DCF(cash, grow_year, grow_rate, permanent_rate, discount):
    cash_rate = 1 + ((grow_rate - discount) / 100)

    total_cash_rate = 0
    max_cash_rate_year = 0
    # 增长现金流
    for i in range(grow_year):
        total_cash_rate += cash_rate ** i
        max_cash_rate_year = cash_rate ** i

    # 永续现金流
    for i in range(50):  # 永续增长
        total_cash_rate += max_cash_rate_year * (1 + (permanent_rate / 100)) * (1 - (discount / 100)) ** i

    return cash * total_cash_rate

# 投资回报率(按芒格说法，按PB=1买入一个公司，则投资回报率等于净资产收益率)
def ROIC(roic=0.0, pb=1000, grow=-100) -> float:
    result = 0.0
    try:
        result = roic / pb * (1 + (grow / 100))
    except TypeError:
        # print('ROIC, ', ValueError)
        pass
    return result

# 以DCF和ROIC筛选出优质且低估的企业
# 选股条件
# 市净率<10；
# 总市值为>100亿；
# 每股经营现金流为>1：
# 投入资本回报率ROIC为>5%；
# 净利率为>10%；
# 净利润3年复合增长率为>10%；
# 营收3年复合增长率为>10%；
# 预测净利润同比增长为>10%；
# 预测营收同比增长为>10%；
# 上市以来年化收益率为>10%

# (PBNEWMRQ>0)(PBNEWMRQ<=10)(TOTAL_MARKET_CAP>10000000000)(ROIC>10)(SALE_NPR>10)(NETPROFIT_GROWTHRATE_3Y>10)(INCOME_GROWTHRATE_3Y>10)(PREDICT_NETPROFIT_RATIO>10)(PREDICT_INCOME_RATIO>10)(PER_NETCASH_OPERATE>1)
# (PBNEWMRQ>0)(PBNEWMRQ<=10)(TOTAL_MARKET_CAP>1000000000)(ROIC>5)(SALE_NPR>10)(NETPROFIT_GROWTHRATE_3Y>0)(INCOME_GROWTHRATE_3Y>0)(PREDICT_NETPROFIT_RATIO>0)(PREDICT_INCOME_RATIO>0)(PER_NETCASH_OPERATE>1)
# (PBNEWMRQ<=10)(PE9<40)(TOTAL_MARKET_CAP>10000000000)(ROIC>5)(SALE_NPR>10)(NETPROFIT_GROWTHRATE_3Y>-5)(INCOME_GROWTHRATE_3Y>-5)(PREDICT_NETPROFIT_RATIO>0)(PREDICT_INCOME_RATIO>0)(PER_NETCASH_OPERATE>1)
uri = "https://datacenter.eastmoney.com/stock/selection/api/data/get/"
d = {
    "type": "RPTA_SECURITY_STOCKSELECT",
    "sty": "ECURITY_CODE,SECURITY_NAME_ABBR,NEW_PRICE,PBNEWMRQ,ROIC,NETPROFIT_GROWTHRATE_3Y,INCOME_GROWTHRATE_3Y,PREDICT_NETPROFIT_RATIO,PREDICT_INCOME_RATIO,SALE_NPR,PER_NETCASH_OPERATE,TOTAL_MARKET_CAP,PE9,TOTAL_MARKET_CAP,ROIC",
    "filter": '(MARKET IN ("上交所主板","深交所主板","深交所创业板","上交所科创板","上交所风险警示板","深交所风险警示板","北京证券交易所"))(PBNEWMRQ<=10)(PE9>0)(PE9<50)(TOTAL_MARKET_CAP>10000000000)',
    "p": 1,
    "ps": 5000,
    "sr": -1,
    "st": "TOTAL_MARKET_CAP",
    "source": "SELECT_SECURITIES",
    "client": "WEB",
}
r = requests.post(uri, data=d)
if r.status_code != 200:
    raise Exception("status_code: ", r.status_code)

data = r.json()["result"]["data"]

Million = 1000*1000
Billion = 1000*Million
print('datalen: ', len(r.json()["result"]["data"]))
# print(['NAME', 'NEW_PRICE', 'PB', 'PE', 'ROIC', 'GROW', 'ROIC_RETURN', 'ROIC_PRICE', 'DCF_PRICE', 'SCORE', '市赚率'])
print(['NAME', 'NEW_PRICE', 'PB', 'PE', 'GROW', 'DCF_PRICE', 'SCORE', 'ROIC'])
for i in r.json()["result"]["data"]:
    try:
        # ROIC
        # 非常非常保守的增长率估算: MIN(过去3年平均增长率的1/3,分析师预估未来的增长率的1/2)
        GROWTHRATE = min(i['NETPROFIT_GROWTHRATE_3Y']*1.0 / 2.0, i['INCOME_GROWTHRATE_3Y']*1 / 3)

        roic = 1
        if i['ROIC']:
            roic = i['ROIC']
        # else:
        #     print('NO roic in: ', i)
        ROIC_RETURN = ROIC(roic, i['PBNEWMRQ'], GROWTHRATE)
        # # 以长期投资回报率5%为分界, 计算合理估值
        #
        ROIC_PRICE = ROIC_RETURN / 5.0 * i['NEW_PRICE']
        #
        # # DCF
        # # 以 净利润/ROIC/当前规模 判断公司的增长潜力, 高利润率，市值1000亿以下企业认为增长更久
        CASH_PER = 1 + ((GROWTHRATE - 10) / 100)
        GROW_YEAR = 5  # 利润率低，增长5年
        if i['SALE_NPR'] > 50 and roic > 30 and i['TOTAL_MARKET_CAP'] < 10*Billion:  # 利润率高，增长10年
            GROW_YEAR = 10
        #
        CASH_PRICE = DCF(i['PER_NETCASH_OPERATE'] * 1.35, GROW_YEAR, GROWTHRATE, 3, 10)
        # SCORE = (CASH_PRICE / i['NEW_PRICE'] + ROIC_PRICE / i['NEW_PRICE']) / 2
        SCORE = CASH_PRICE / i['NEW_PRICE']
        PR = i['PE9']/roic
        if ROIC_RETURN > 5 and PR < 2:
        # if ROIC_RETURN > 2 and i['ROIC'] > 10 and PR < 1 and i['TOTAL_MARKET_CAP'] > 10000000000:

        # if i['PBNEWMRQ'] < 1:
            # print('i:', i)
            print([i['SECURITY_NAME_ABBR'], i['NEW_PRICE'], i['PBNEWMRQ'], i['PE9'], GROWTHRATE, CASH_PRICE, SCORE, roic])
    except:
        print("except:", i)

# dcf_value = DCF(650, 5, 15, 3, 10)
# print("DCF:", dcf_value)