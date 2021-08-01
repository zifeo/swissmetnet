import argparse
import logging
from os import environ

import pymongo
from swissmetnet import data
from swissmetnet import utils

logging.getLogger().setLevel(logging.INFO)

db = pymongo.MongoClient(host=environ["MONGO_URI"]).swissmetnet

datasets = {
    "vqha80": data.read_vqha80,
    "vqha98": data.read_vqha98,
    "cosmo2e": data.read_cosmoe2,
}

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--data", nargs="+", choices=datasets.keys(), required=True)

for ds in parser.parse_args().data:
    utils.upsert_mongo(db, ds, datasets[ds]())
