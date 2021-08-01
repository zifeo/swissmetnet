import logging
from os import environ

import pymongo
from swissmetnet import data
from swissmetnet import utils

logging.getLogger().setLevel(logging.INFO)

db = pymongo.MongoClient(host=environ["MONGO_URI"]).swissmetnet

utils.upsert_mongo(db, "vqha80", data.read_vqha80())
utils.upsert_mongo(db, "vqha98", data.read_vqha98())
utils.upsert_mongo(db, "cosmo2e", data.data.read_cosmoe2())
