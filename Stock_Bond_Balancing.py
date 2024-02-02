import time
import xmltodict
import requests
# 对比中美国债/中美大盘指数的投资性价比


# 国债 https://data.eastmoney.com/cjsj/zmgzsyl.html
def get_cn_bonds():
    cn_bonds_uri = "https://iftp.chinamoney.com.cn/ags/ms/cm-u-bk-currency/SddsIntrRateGovYldHis?lang=CN&pageNum=1&pageSize=5"
    header = {
        "X-Forwarded-For": "1.1.1.1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    reply = requests.get(cn_bonds_uri, headers=header)
    if reply.status_code != 200:
        print(reply.text)
        raise Exception("get cn_bonds_uri status_code:", reply.status_code)
    record = reply.json()['records'][0]
    oneRate = str(round(float(record['oneRate']), 2))+'%'
    tenRate = str(round(float(record['tenRate']), 2))+'%'
    print('中国1年期国债利率:', oneRate, '中国10年期国债利率:', tenRate)


def get_us_bonds():
    us_bonds_uri = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2024"
    reply = requests.get(us_bonds_uri)
    if reply.status_code != 200:
        raise Exception("get us_bonds_uri status_code:", reply.status_code)

    us_bonds_data = xmltodict.parse(reply.text)
    properties = us_bonds_data['feed']['entry'][-1]['content']['m:properties']
    print('美国1年期国债利率:', properties['d:BC_1YEAR']['#text']+'%', '美国10年期国债利率:', properties['d:BC_10YEAR']['#text']+'%')


# 宽基指数 https://danjuanfunds.com/djapi/index_eva/dj
def get_index():
    index_uri = "https://danjuanfunds.com/djapi/index_eva/dj"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    reply = requests.get(index_uri, headers=header)
    if reply.status_code != 200:
        raise Exception("get index_uri status_code:", reply.status_code)
    # 'CSIH30533', 'SH000852', 'HKHSI', 'SH000905'
    index_codes = set(['SH000300', 'SP500', 'NDX', 'HKHSTECH'])
    for i in reply.json()['data']['items']:
        # print(i)
        if i['index_code'] in index_codes:
            pe_per = "{:.2%}".format(round(1 - float(i['pe_over_history']), 3))
            pb_per = "{:.2%}".format(round(1 - float(i['pb_over_history']), 3))
            roe_pb = round(i['roe'] / i['pb'], 4)
            print(i['index_code'], i['name'], ': PE:', round(i['pe'], 3), ', PB:', round(i['pb'], 3), ', ROE:', "{:.2%}".format(round(i['roe'], 4)),
                  ', PE百分位:', pe_per, ', PB百分位:', pb_per, ', 股息率:', "{:.2%}".format(i['yeild']), ', ROE/PB:', "{:.2%}".format(roe_pb))


date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
print('\n')
print('DATE:', date, '汇率(USD/CNY):', response.json()['rates']['CNY'])

get_cn_bonds()
get_us_bonds()
get_index()