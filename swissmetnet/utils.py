import json
import logging

import pymongo


def insert_once_mongo(db, collection, df):
    """
    Insert only once the dataframe into Mongo (assume there is a unique index set to avoid any duplicates).
    """
    logging.info(f"saving {collection}: {df.shape}")
    try:
        db[collection].insert_many(
            json.loads(df.to_json(orient="records")), ordered=False
        )
    except pymongo.errors.BulkWriteError as err:
        if any([e["code"] != 11000 for e in err.details["writeErrors"]]):
            raise err
        else:
            logging.info(f"duplicates ignored: {len(err.details['writeErrors'])}")
