import logging

import pymongo


def upsert_mongo(db, collection, df):
    logging.info(f"reading {collection}: {len(df.shape)}")
    try:
        db[collection].insert_many(df.to_dict(orient="records"), ordered=False)
    except pymongo.errors.BulkWriteError as err:
        if any([e["code"] != 11000 for e in err.details["writeErrors"]]):
            raise err
