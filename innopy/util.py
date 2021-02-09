import json
from collections import namedtuple

def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)

def list_to_id_dict(list):
    list_dict = {}
    for item in list:
        if "id" in item:
            list_dict[item["id"]]=item
        elif "Id" in item:
            list_dict[item["Id"]]=item
        else:
            raise Exception("no id attribute found")
    return list_dict
