import io
import json
import logging
from os import environ

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import pandas as pd
import pymongo

_MONGO_BATCH = 2000


def _records(df):
    payload = df.copy()
    for col in payload.columns:
        if pd.api.types.is_datetime64_any_dtype(payload[col]):
            series = payload[col]
            ms = series.astype("datetime64[ms]").astype("int64")
            payload[col] = pd.Series(ms, index=series.index, dtype="Int64").where(
                series.notna(), pd.NA
            )
    return json.loads(payload.to_json(orient="records"))


class Mongo:
    def __init__(self) -> None:
        self.db = pymongo.MongoClient(host=environ["MONGO_URI"]).swissmetnet

    def insert_once(self, name, df):
        """
        Insert only once the dataframe into Mongo (assume there is a unique index set to avoid any duplicates).
        """
        logging.info(f"saving {name}: {df.shape}")
        ignored = 0
        for start in range(0, len(df), _MONGO_BATCH):
            end = start + _MONGO_BATCH
            batch = _records(df.iloc[start:end])
            try:
                self.db[name].insert_many(batch, ordered=False)
            except pymongo.errors.BulkWriteError as err:
                write_errors = err.details.get("writeErrors") or []
                if err.details.get("writeConcernErrors") or any(
                    e["code"] != 11000 for e in write_errors
                ):
                    raise
                ignored += len(write_errors)
        if ignored:
            logging.info(f"duplicates ignored: {ignored}")
        else:
            logging.info(f"saved {name}: {df.shape}")


def _s3_is_404(err):
    status = err.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
    code = str(err.response.get("Error", {}).get("Code", ""))
    return status == 404 or code in {"404", "NotFound", "NoSuchKey", "NoSuchBucket"}


class S3:
    def __init__(self) -> None:
        self.bucket = environ["S3_BUCKET"]
        self.endpoint = environ.get("S3_ENDPOINT") or None
        self._ensured = False
        self.client = boto3.client(
            "s3",
            region_name=environ["S3_REGION"],
            aws_access_key_id=environ.get("S3_ACCESS_KEY") or None,
            aws_secret_access_key=environ.get("S3_SECRET_KEY") or None,
            aws_session_token=environ.get("S3_SESSION_TOKEN") or None,
            config=Config(
                signature_version=environ.get("S3_ENDPOINT_SIGNATURE", "s3v4"),
                s3={"addressing_style": "path"} if self.endpoint else {},
            ),
            **({"endpoint_url": self.endpoint} if self.endpoint else {}),
        )

    def ensure_bucket(self):
        if not self.endpoint or self._ensured:
            return
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as err:
            if not _s3_is_404(err):
                raise
            self.client.create_bucket(Bucket=self.bucket)
        self._ensured = True

    def exists(self, key):
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except ClientError as err:
            if _s3_is_404(err):
                return False
            raise
        return True

    def list_keys(self, prefix):
        keys = set()
        try:
            pages = self.client.get_paginator("list_objects_v2").paginate(
                Bucket=self.bucket, Prefix=prefix
            )
            for page in pages:
                for obj in page.get("Contents") or []:
                    keys.add(obj["Key"])
        except ClientError as err:
            if not _s3_is_404(err):
                raise
        return keys

    def put_bytes(self, key, body, content_type="application/octet-stream"):
        self.ensure_bucket()
        logging.info("saving %s", key)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )
        logging.info("saved %s", key)

    def insert_once(self, name, df):
        col = df["issueAt"] if "issueAt" in df.columns else df["Date"]
        stamp = col.dropna().max()
        if pd.isna(stamp):
            raise RuntimeError(f"{name}: empty timestamp column")
        key = f"{name}/{stamp.isoformat()}.parquet"
        if self.exists(key):
            logging.info("exists %s", key)
            return
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=False)
        self.put_bytes(key, buffer.getvalue(), "application/vnd.apache.parquet")
