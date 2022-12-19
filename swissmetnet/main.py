import argparse
import logging

from swissmetnet import data
from swissmetnet import stores

logging.getLogger().setLevel(logging.INFO)


def run():
    datasets = {
        name[5:]: getattr(data, name) for name in dir(data) if name.startswith("read_")
    }
    storages = {
        "mongo": stores.Mongo,
        "s3": stores.S3,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--data", nargs="+", choices=datasets.keys(), required=True
    )
    parser.add_argument("-s", "--storage", choices=storages.keys(), required=True)
    args = parser.parse_args()

    storage = storages[args.storage]()
    for ds in parser.parse_args().data:
        storage.insert_once(ds, datasets[ds]())


if __name__ == "__main__":
    run()
