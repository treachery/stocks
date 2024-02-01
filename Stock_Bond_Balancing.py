import time
import xmltodict
import requests


# 对比中美国债/中美大盘指数的投资性价比
def float3(f: float):
    return format(f, '.3f')


def float4(f: float):
    return format(f, '.4f')

# 国债 https://data.eastmoney.com/cjsj/zmgzsyl.html
def get_cn_bonds():
    cn_bonds_uri = "https://iftp.chinamoney.com.cn/ags/ms/cm-u-bk-currency/SddsIntrRateGovYldHis?lang=CN&pageNum=1&pageSize=5"
    reply = requests.get(cn_bonds_uri)
    if reply.status_code != 200:
        raise Exception("get cn_bonds_uri status_code:", reply.status_code)
    record = reply.json()['records'][0]
    print('中国1年期国债利率:',  float3(float(record['oneRate'])))
    print('中国10年期国债利率:', float3(float(record['tenRate'])))


def get_us_bonds():
    us_bonds_uri = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2024"
    reply = requests.get(us_bonds_uri)
    if reply.status_code != 200:
        raise Exception("get us_bonds_uri status_code:", reply.status_code)

    us_bonds_data = xmltodict.parse(reply.text)
    properties = us_bonds_data['feed']['entry'][-1]['content']['m:properties']
    print('美国1年期国债利率:', properties['d:BC_1YEAR']['#text'])
    print('美国10年期国债利率:', properties['d:BC_10YEAR']['#text'])


# 宽基指数 https://danjuanfunds.com/djapi/index_eva/dj
def get_index():
    index_uri = "https://danjuanfunds.com/djapi/index_eva/dj"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    reply = requests.get(index_uri, headers=header)
    if reply.status_code != 200:
        raise Exception("get index_uri status_code:", reply.status_code)
    for i in reply.json()['data']['items']:
        if i['index_code'] == "HKHSI" or i['index_code'] == "SH000300" or i['index_code'] == "SH000905" or i['index_code'] == "SH000852" or i['index_code'] == "SP500" or i['index_code'] == "NDX" or i['index_code'] == "CSIH30533":
            pe_per = float3(1 - float(i['pe_over_history']))
            pb_per = float3(1 - float(i['pb_over_history']))
            roe_pb = float4(i['roe'] / i['pb'])
            print(i['name'], ': PE:', float3(i['pe']), ', PB:', float3(i['pb']), ', ROE:', float4(i['roe']),
                  ', PE百分位:', pe_per, ', PB百分位:', pb_per, ', 股息率:', i['yeild'], ', ROE/PB:', roe_pb)


date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
print('\n')
print('DATE:', date, '汇率(USD/CNY):', response.json()['rates']['CNY'])

get_cn_bonds()
get_us_bonds()
get_index()
