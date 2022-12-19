import argparse
import logging
from os import environ

import pymongo
from swissmetnet import data
from swissmetnet import utils

logging.getLogger().setLevel(logging.INFO)


def run():
    db = pymongo.MongoClient(host=environ["MONGO_URI"]).swissmetnet
    datasets = {
        name[5:]: getattr(data, name) for name in dir(data) if name.startswith("read_")
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--data", nargs="+", choices=datasets.keys(), required=True
    )

    for ds in parser.parse_args().data:
        utils.insert_once_mongo(db, ds, datasets[ds]())


if __name__ == "__main__":
    run()
