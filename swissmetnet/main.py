import logging
from os import environ

import pymongo
from swissmetnet import data

logging.getLogger().setLevel(logging.INFO)

db = pymongo.MongoClient(host=environ["MONGO_URI"]).swissmetnet


def upsert_mongo(db, collection, df):
    logging.info(f"reading {collection}: {len(df.shape)}")
    try:
        db[collection].insert_many(df.to_dict(orient="records"), ordered=False)
    except pymongo.errors.BulkWriteError as err:
        if any([e["code"] != 11000 for e in err.details["writeErrors"]]):
            raise err


upsert_mongo(db, "vqha80", data.read_vqha80())
upsert_mongo(db, "vqha98", data.read_vqha98())
upsert_mongo(db, "cosmo2e", data.data.read_cosmoe2())
