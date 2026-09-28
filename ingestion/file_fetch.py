import json

def load_data_from_file(path="data1.jsonl"):
    records = []
    with open(path,"r") as f:
        for line in f:
            records.append(json.loads(line))
    return records