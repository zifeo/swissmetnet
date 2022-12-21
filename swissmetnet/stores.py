import io
import json
import logging
from os import environ

import boto3
import pymongo


class Mongo:
    def __init__(self) -> None:
        self.db = pymongo.MongoClient(host=environ["MONGO_URI"]).swissmetnet

    def insert_once(self, name, df):
        """
        Insert only once the dataframe into Mongo (assume there is a unique index set to avoid any duplicates).
        """
        logging.info(f"saving {name}: {df.shape}")
        try:
            self.db[name].insert_many(
                json.loads(df.to_json(orient="records")), ordered=False
            )
            logging.info(f"saved {name}: {df.shape}")
        except pymongo.errors.BulkWriteError as err:
            if any([e["code"] != 11000 for e in err.details["writeErrors"]]):
                raise err
            else:
                logging.info(f"duplicates ignored: {len(err.details['writeErrors'])}")


class S3:
    def __init__(self) -> None:
        from botocore.config import Config

        self.client = boto3.client(
            "s3",
            region_name=environ["S3_REGION"],
            aws_access_key_id=environ.get("S3_ACCESS_KEY", ""),
            aws_secret_access_key=environ.get("S3_SECRET_KEY", ""),
            aws_session_token=environ.get("S3_SESSION_TOKEN", ""),
            verify="https" in environ.get("S3_ENDPOINT", "https"),
            config=Config(
                signature_version=environ.get("S3_ENDPOINT_SIGNATURE", "s3v4")
            ),
            **{"endpoint_url": environ["S3_ENDPOINT"]}
            if "S3_ENDPOINT" in environ
            else {},
        )

    def insert_once(self, name, df):
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        readAt = df.Date.iloc[0].isoformat()
        logging.info(f"saving {name}: {df.shape}")
        self.client.put_object(
            Bucket=environ["S3_BUCKET"],
            Key=f"{name}/{readAt}.parquet",
            Body=buffer.getvalue(),
        )
        logging.info(f"saved {name}: {df.shape}")
