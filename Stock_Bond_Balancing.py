import time
import xmltodict
import requests
from wcwidth import wcswidth
# 对比中美国债/中美大盘指数的投资性价比

# 国债 https://data.eastmoney.com/cjsj/zmgzsyl.html
def get_cn_bonds():
    requests.get("https://iftp.chinamoney.com.cn/chinese/sddsintigy/")

    cn_bonds_uri = "https://iftp.chinamoney.com.cn/ags/ms/cm-u-bk-currency/SddsIntrRateGovYldHis?lang=CN&pageNum=1&pageSize=5"
    header = {
        "X-Forwarded-For": "1.1.1.1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin":"https://iftp.chinamoney.com.cn",
        "Referer":"https://iftp.chinamoney.com.cn/chinese/sddsintigy/"
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
    return max(float(properties['d:BC_1YEAR']['#text']), float(properties['d:BC_10YEAR']['#text']))
    # return float(properties['d:BC_10YEAR']['#text'])

def pad_cjk(text, target_display_width):
    current_width = wcswidth(text)
    return text + ' ' * (target_display_width - current_width) if current_width < target_display_width else text

# 宽基指数 https://danjuanfunds.com/djapi/index_eva/dj
def get_index(max_rate: float):
    index_uri = "https://danjuanfunds.com/djapi/index_eva/dj"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    reply = requests.get(index_uri, headers=header)
    if reply.status_code != 200:
        raise Exception("get index_uri status_code:", reply.status_code)
    # 'CSIH30533', 'SH000852', 'HKHSI', 'SH000905'
    index_codes = set(['SH000300', 'SP500', 'NDX', 'HKHSTECH', 'HKHSCEI', 'SZ399989', 'SZ399997','CSIH30533'])

    rate_10y = (max_rate/100+1)**10
    # print('当前国债收益率:', max_rate, ', 国债10年复利:', round(rate_10y, 3))
    for i in reply.json()['data']['items']:
        if i['index_code'] in index_codes:
            # print(i)
            pe_per = "{:.2%}".format(round(1 - float(i['pe_over_history']), 3))
            pb_per = "{:.2%}".format(round(1 - float(i['pb_over_history']), 3))
            roe_pb = round(i['roe'] / i['pb'], 4)

            # 建议仓位（综合考虑了国债收益率，ROE和估值的关系）, 我们认为2倍国债收益率的ROE是安全边界，低于该值就完全不值得投资
            # ROE虽然好，但要警惕苹果公司这种靠金融操作、债务杠杆推高收益率的公司
            _suggested_position = 0
            rate_per = (max_rate/100)
            if i['roe'] > rate_per:
                # roe_x = 1 + ((i['roe'] / (3*rate_per)) / (i['roe'] + 3*rate_per)) # 认为roe > 3倍无风险利率是分界，高于赚的是easy money，享受额外加成
                # pe_h = (0.5 + float(i['pe_over_history'])) # pe百分位低于50%则加成更高
                # pg_x = i['pe']/(i['roe']*100) # 市赚率, 市赚率大于1高估，小于1低估
                # rate_x = rate_per + 1
                # eg_x = 1/i['pe']/pg_x # 预期收益率
                # if eg_x > 3*rate_per: # 满仓
                #     sp_x = 1
                # elif eg_x > rate_per:
                #     sp_x = 0.5 + (eg_x - rate_per) / (4 * rate_per)
                # elif eg_x <= rate_per/2: # 空仓
                #     sp_x = 0
                # else:
                #     sp_x = 0.5 + (eg_x-rate_per)*3 / (4 * rate_per)
                roe_pb_x = round(((i['roe']) / 0.15) * i['roe'] / i['pb'], 4)

                # _suggested_position = (roe_pb_x - rate_per) / (roe_pb_x + rate_per)  #* pe_h

                # print('roe_x:', roe_x, ', pe_h:', 0, ', pg_x:', pg_x, ', rate_x:', rate_x, ', eg_x:', eg_x, ' ,sp_x:', sp_x)
            # if _suggested_position > 0:
                # print(i)
            # if i['pe'] < 20 and i['pb'] < 1:
            #     "{:<9}".format(i['index_code']),
                print("{:<9}".format(i['index_code']), ': PE:', "{:>6.3f}".format(round(i['pe'], 3)), ', PB:', round(i['pb'], 3), ', ROE:', "{:.2%}".format(round(i['roe'], 4)),
                      ', PE百分位:', "{:>6}".format(pe_per), ', PB百分位:', "{:>6}".format(pb_per), ', 股息率:', "{:.2%}".format(i['yeild']),
                      ', PB-ROE:', "{:>6.2%}".format(roe_pb), ', 预期收益率(修正PB-ROE):', "{:.1%}".format(roe_pb_x), pad_cjk(i['name'], 8))

date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')

print('\n\nDATE:', date, '汇率(USD/CNY):', response.json()['rates']['CNY'])

# get_cn_bonds()
max_rate = get_us_bonds()
print('\n说明: 以ROE=15为分界，高于赚的是easy money，享受额外加成\n')

get_index(max_rate)