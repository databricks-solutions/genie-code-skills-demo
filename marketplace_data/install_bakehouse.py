# Databricks notebook source
# MAGIC %md
# MAGIC # Install / Mirror AI/BI Bakehouse for the Sentiment Demo
# MAGIC
# MAGIC The Stage 5 demo reads from `<demo_catalog>.<bakehouse_schema>` so the
# MAGIC sentiment-analysis pipeline lives next to the synthetic financial data.
# MAGIC
# MAGIC This notebook is **detect-then-install**:
# MAGIC
# MAGIC 1. Probe a list of candidate Bakehouse catalogs to see if any are already
# MAGIC    readable as the current user. Shared / field demo workspaces almost
# MAGIC    always have Bakehouse pre-installed under one of these names, so a
# MAGIC    fresh Marketplace install is unnecessary in those cases.
# MAGIC 2. If none are readable, fall back to installing the Marketplace share
# MAGIC    into a scratch catalog via the Marketplace REST API.
# MAGIC 3. CTAS-mirror the tables we use into `<demo_catalog>.<bakehouse_schema>`.
# MAGIC
# MAGIC The mirror step is idempotent (`CREATE OR REPLACE TABLE`).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

dbutils.widgets.text("scratch_catalog_name", "bakehouse_share_scratch", "Scratch Catalog (Marketplace fallback target)")
dbutils.widgets.text("listing_name", "bakehouse", "Marketplace Listing Name (substring matched against name+subtitle)")
dbutils.widgets.text("share_provider_name", "databricks", "Share Provider Name (filter, currently informational)")
dbutils.widgets.text("demo_catalog", "", "Demo Catalog (existing) - mirror destination")
dbutils.widgets.text("demo_schema", "bakehouse", "Demo Schema (created if missing)")
dbutils.widgets.text(
    "candidate_source_catalogs",
    "bakehouse",
    "Comma-separated list of catalog names to probe for an existing Bakehouse share",
)
dbutils.widgets.text(
    "consumer_terms_version",
    "2023-01",
    "Marketplace consumer-terms version (e.g. '2023-01')",
)

SCRATCH_CATALOG = dbutils.widgets.get("scratch_catalog_name").strip()
LISTING_NAME = dbutils.widgets.get("listing_name").strip()
SHARE_PROVIDER_NAME = dbutils.widgets.get("share_provider_name").strip().lower()
DEMO_CATALOG = dbutils.widgets.get("demo_catalog").strip()
DEMO_SCHEMA = dbutils.widgets.get("demo_schema").strip()
CONSUMER_TERMS_VERSION = dbutils.widgets.get("consumer_terms_version").strip() or "2023-01"

CANDIDATE_CATALOGS = [
    c.strip()
    for c in dbutils.widgets.get("candidate_source_catalogs").split(",")
    if c.strip()
]
if SCRATCH_CATALOG and SCRATCH_CATALOG not in CANDIDATE_CATALOGS:
    CANDIDATE_CATALOGS.append(SCRATCH_CATALOG)

if not DEMO_CATALOG or not DEMO_SCHEMA:
    raise ValueError("demo_catalog and demo_schema are required.")

print(f"Candidate source catalogs: {CANDIDATE_CATALOGS}")
print(f"Scratch (fallback) catalog: {SCRATCH_CATALOG}")
print(f"Mirror target:              {DEMO_CATALOG}.{DEMO_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1 -- Detect an Already-Accessible Bakehouse Catalog
# MAGIC
# MAGIC We probe each candidate by trying a one-row read of the canonical reviews
# MAGIC table. The first one that succeeds becomes our source.

# COMMAND ----------

from pyspark.sql.utils import AnalysisException

PROBE_TABLE = "media.customer_reviews"


def probe_catalog(catalog: str) -> bool:
    try:
        spark.sql(f"SELECT 1 FROM {catalog}.{PROBE_TABLE} LIMIT 1").collect()
        return True
    except AnalysisException as exc:
        print(f"  {catalog}: not readable ({type(exc).__name__})")
        return False
    except Exception as exc:
        print(f"  {catalog}: not readable ({type(exc).__name__}: {exc!s:.120})")
        return False


source_catalog = None
print("Probing candidate catalogs...")
for candidate in CANDIDATE_CATALOGS:
    if probe_catalog(candidate):
        source_catalog = candidate
        print(f"  {candidate}: OK -- using as source")
        break

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2 -- (Fallback) Install the Marketplace Share
# MAGIC
# MAGIC Only runs if no candidate catalog was readable.

# COMMAND ----------

if source_catalog is None:
    import json
    import time

    import requests

    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    HOST = ctx.apiUrl().get()
    TOKEN = ctx.apiToken().get()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {TOKEN}"})

    print(f"No accessible Bakehouse catalog found. Attempting Marketplace install into '{SCRATCH_CATALOG}'.")

    listing_id = None
    listing_name_resolved = None
    next_page_token = None
    listing_name_lower = LISTING_NAME.lower()
    while True:
        params = {"page_size": 50, "query": LISTING_NAME}
        if next_page_token:
            params["page_token"] = next_page_token
        resp = session.get(
            f"{HOST}/api/2.1/marketplace-consumer/search-listings",
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        body = resp.json()
        for listing in body.get("listings", []):
            summary = listing.get("summary", {}) or {}
            name = (summary.get("name") or "").strip()
            subtitle = (summary.get("subtitle") or "").strip()
            haystack = f"{name} {subtitle}".lower()
            if listing_name_lower not in name.lower() and listing_name_lower not in haystack:
                continue
            listing_id = listing.get("id")
            listing_name_resolved = name
            break
        if listing_id or not body.get("next_page_token"):
            break
        next_page_token = body["next_page_token"]

    if not listing_id:
        raise RuntimeError(
            f"No Marketplace listing matched query '{LISTING_NAME}' and no candidate "
            f"catalog ({CANDIDATE_CATALOGS}) is readable. Either grant the running "
            f"user access to an existing Bakehouse share or set listing_name to "
            f"match the actual listing in your workspace's Marketplace."
        )

    print(f"Matched Marketplace listing: '{listing_name_resolved}' (id={listing_id})")

    fulfill_resp = session.get(
        f"{HOST}/api/2.1/marketplace-consumer/listings/{listing_id}/fulfillments",
        timeout=60,
    )
    fulfill_resp.raise_for_status()
    share_name = None
    for f in fulfill_resp.json().get("fulfillments", []):
        share_info = f.get("share_info") or {}
        if share_info.get("name"):
            share_name = share_info["name"]
            break
    if not share_name:
        raise RuntimeError(
            f"Listing '{listing_name_resolved}' has no share-based fulfillment; cannot install."
        )

    print(f"Share name: {share_name}")
    print(f"Accepting consumer terms version: {CONSUMER_TERMS_VERSION}")
    install_resp = session.post(
        f"{HOST}/api/2.1/marketplace-consumer/listings/{listing_id}/installations",
        data=json.dumps({
            "catalog_name": SCRATCH_CATALOG,
            "share_name": share_name,
            "accepted_consumer_terms": {"version": CONSUMER_TERMS_VERSION},
        }),
        timeout=120,
    )
    if not install_resp.ok:
        raise RuntimeError(f"Marketplace install failed: {install_resp.status_code} {install_resp.text}")

    for _ in range(30):
        if probe_catalog(SCRATCH_CATALOG):
            source_catalog = SCRATCH_CATALOG
            break
        time.sleep(2)

    if source_catalog is None:
        raise RuntimeError(f"Catalog '{SCRATCH_CATALOG}' did not become readable after install.")

    print(f"Marketplace install complete. Using '{SCRATCH_CATALOG}' as source.")

print(f"Source catalog resolved: {source_catalog}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3 -- Mirror Tables Into the Demo Catalog/Schema

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {DEMO_CATALOG}.{DEMO_SCHEMA}")
print(f"Schema ready: {DEMO_CATALOG}.{DEMO_SCHEMA}")

MIRROR_TABLES = [
    ("media.customer_reviews", "customer_reviews"),
    ("sales.franchises", "franchises"),
    ("sales.transactions", "transactions"),
    ("sales.customers", "customers"),
]

mirrored = []
for source_relative, target_table in MIRROR_TABLES:
    source = f"{source_catalog}.{source_relative}"
    target = f"{DEMO_CATALOG}.{DEMO_SCHEMA}.{target_table}"
    try:
        print(f"Mirroring {source} -> {target}")
        spark.sql(f"CREATE OR REPLACE TABLE {target} AS SELECT * FROM {source}")
        mirrored.append(target_table)
    except Exception as exc:
        print(f"  WARNING: skipping {source}: {type(exc).__name__}: {exc!s:.200}")

if "customer_reviews" not in mirrored:
    raise RuntimeError(
        f"customer_reviews could not be mirrored from {source_catalog} -- the demo "
        "depends on this table. Aborting."
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify

# COMMAND ----------

display(spark.sql(f"SHOW TABLES IN {DEMO_CATALOG}.{DEMO_SCHEMA}"))

print("Row counts:")
for target_table in mirrored:
    n = spark.sql(f"SELECT COUNT(*) AS n FROM {DEMO_CATALOG}.{DEMO_SCHEMA}.{target_table}").collect()[0]["n"]
    print(f"  {target_table}: {n}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC
# MAGIC The Stage 5 demo prompts read from `<demo_catalog>.<bakehouse_schema>`,
# MAGIC e.g. `genie_code_skills_demo.bakehouse.customer_reviews`.

dbutils.notebook.exit(
    f"source:{source_catalog}|mirrored:{DEMO_CATALOG}.{DEMO_SCHEMA}|tables:{','.join(mirrored)}"
)
