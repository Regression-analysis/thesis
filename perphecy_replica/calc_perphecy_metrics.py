import pymongo
from pymongo import MongoClient

def calc_perphecy_metrics(commitsha_1, commitsha_2):
    client = MongoClient()
    db = client.research

    dynamic_data_1 = db.commitprofiles.find_one({ "commitsha": commitsha_1 })
    dynamic_data_2 = db.commitprofiles.find_one({ "commitsha": commitsha_2 })
