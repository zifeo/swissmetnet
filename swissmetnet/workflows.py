import asyncio
import itertools
import logging
from os import environ
from urllib.parse import urlparse

import substantial as s
from swissmetnet import data
from swissmetnet import stores

_STORE_NS = "substantial"
_S3_SCHEMES = ("s3://", "s3+http://", "h3://", "h3+http://")
_LIST_RETRY = s.Retry(
    max_attempts=3, initial=s.seconds(1), max=s.seconds(8), multiplier=2
)
_COPY_RETRY = s.Retry(
    max_attempts=5, initial=s.seconds(2), max=s.minutes(2), multiplier=2
)


def _copy_asset(storage, asset, ref):
    if storage.exists(asset["key"]):
        return asset["key"]
    storage.put_bytes(asset["key"], data.icon_grib_bytes(asset, ref))
    return asset["key"]


def _build_workflow(storage):
    @s.workflow
    async def ingest_icon_ch2e(c: s.Context, ref: str) -> dict:
        assets = await c.step(
            "list_icon_assets",
            data.icon_asset_list,
            ref,
            retry=_LIST_RETRY,
            timeout=s.minutes(2),
        )
        for batch in itertools.batched(assets, 4):
            await asyncio.gather(
                *(
                    c.step(
                        "copy_icon_asset",
                        _copy_asset,
                        storage,
                        asset,
                        ref,
                        retry=_COPY_RETRY,
                        timeout=s.minutes(10),
                    )
                    for asset in batch
                )
            )
        return {"ref": ref, "n": len(assets)}

    return ingest_icon_ch2e


def _store_url(storage):
    if environ.get("SUBSTANTIAL_URL"):
        return environ["SUBSTANTIAL_URL"]
    region = storage.region.lower()
    if not storage.endpoint:
        return f"s3://s3.{region}.amazonaws.com/{storage.bucket}/{_STORE_NS}?region={region}"
    parsed = urlparse(storage.endpoint)
    valid = (
        parsed.scheme in {"http", "https"},
        bool(parsed.netloc),
        parsed.path in {"", "/"},
    )
    if not all(valid):
        raise ValueError(f"unsupported S3_ENDPOINT for Substantial: {storage.endpoint}")
    scheme = "s3+http" if parsed.scheme == "http" else "s3"
    return f"{scheme}://{parsed.netloc}/{storage.bucket}/{_STORE_NS}?region={region}"


def _store_credentials(url, storage):
    if not url.startswith(_S3_SCHEMES):
        return None
    return s.Credentials(
        access_key_id=storage.access_key,
        secret_access_key=storage.secret_key,
        session_token=storage.session_token,
    )


async def _run_icon_ch2e(storage):
    if not isinstance(storage, stores.S3):
        raise ValueError("icon_ch2e requires S3 storage")
    ref = data.latest_complete_icon_ref()
    if not ref:
        logging.warning("icon_ch2e: no complete run yet, skip")
        return
    storage.ensure_bucket()
    url = _store_url(storage)
    workflow = _build_workflow(storage)
    run_id = f"icon-ch2e-{ref.replace(':', '').lower()}"
    logging.info("icon_ch2e copying ref %s via %s", ref, url)
    async with s.Substantial.create(
        url, credentials=_store_credentials(url, storage)
    ) as sub:
        run = await sub.start(workflow, {"ref": ref}, id=run_id)
        if await run.status() == s.RunStatus.FAILED:
            logging.warning("icon_ch2e retrying failed run %s", run_id)
            await run.retry()
        async with sub.worker([workflow], preset="script"):
            result = await run.result()
        logging.info("icon_ch2e done %s", result)


def run_icon_ch2e(storage):
    asyncio.run(_run_icon_ch2e(storage))
