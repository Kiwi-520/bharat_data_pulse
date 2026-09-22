import json
from pprint import pprint

markets_seen = []
market_id = {}
current_market_id = 1
commodity_seen = []
commodity_id = {}
current_commodity_id = 1
def market_table(entry):
    if entry['Market'] not in markets_seen:
        market_id[entry['Market']] = {"id": current_market_id, "state": entry["State"], "district":entry['District']}
        markets_seen.append(entry['Market'])

def commodity_table(entry):
    if entry["Commodity"] not in commodity_seen:
        commodity_id[entry['Commodity']] = {"id": current_commodity_id, "code": entry['Commodity_Code']}
        commodity_seen.append(entry['Commodity'])


with open("data1.jsonl", 'r') as f:
    for line in f:
        content = json.loads(line)
        market_table(content)
        count_market = len(market_id)+1
        current_market_id =count_market
        commodity_table(content)
        count_commodity = len(commodity_id)+1
        current_commodity_id =count_commodity
