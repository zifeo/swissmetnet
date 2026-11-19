import argparse
import logging

from swissmetnet import data
from swissmetnet import stores

logging.basicConfig(level=logging.INFO)


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
        "-d",
        "--data",
        nargs="+",
        choices=[*datasets.keys(), "icon_ch2e"],
        required=True,
    )
    parser.add_argument("-s", "--storage", choices=storages.keys(), required=True)
    args = parser.parse_args()

    if "icon_ch2e" in args.data and args.storage != "s3":
        parser.error("icon_ch2e requires --storage s3")

    storage = storages[args.storage]()
    for ds in args.data:
        if ds == "icon_ch2e":
            data.sync_icon_ch2e(storage)
        else:
            storage.insert_once(ds, datasets[ds]())


if __name__ == "__main__":
    run()
