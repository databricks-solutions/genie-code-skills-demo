---
name: sentiment-analysis
description: Build sentiment-analysis datasets in SDP pipelines using built-in Databricks AI functions (ai_analyze_sentiment, ai_classify, ai_extract, ai_summarize, ai_query). Use when creating or modifying tables that derive sentiment, topics, or entities from free-form text such as customer reviews, support tickets, social posts, or call transcripts. Always compose this skill with @table-governance and @sdp-basics, and add @pii-management when the source text or surrounding columns contain personal data.
---

# Sentiment Analysis with AI Functions

Apply this skill when building tables that turn free-form text into structured sentiment / topic / entity columns using Databricks' built-in [AI functions](https://docs.databricks.com/aws/en/large-language-models/ai-functions). This skill assumes the SDP and governance basics are already applied -- it adds AI-function-specific rules on top.

## Skill Composition

| Skill | Required? | Why |
|-------|-----------|-----|
| `@table-governance` | Always | Comments, TBLPROPERTIES, column descriptions, UC tags |
| `@sdp-basics` | Always | Layer prefix, audit columns, constraints, formatting |
| `@pii-management` | When source text or joined columns contain personal data | Reviews can leak names/emails -- mask before exposing |
| `@sentiment-analysis` | This skill | AI-function selection, output schema, cost guardrails |

## Choose the Right AI Function

| Function | When to Use | Output |
|----------|-------------|--------|
| `ai_analyze_sentiment(text)` | Single overall sentiment per row | STRING in `{positive, negative, neutral, mixed}` |
| `ai_classify(text, ARRAY('a','b',...))` | Bucket text into a fixed taxonomy (topics, intents) | STRING from the supplied label set |
| `ai_extract(text, ARRAY('field1','field2'))` | Pull named entities or fields out of text | STRUCT<field1:STRING, field2:STRING, ...> |
| `ai_summarize(text, max_words)` | Compress long text into a short blurb | STRING |
| `ai_translate(text, lang)` | Normalize multilingual input before sentiment | STRING |
| `ai_query(endpoint, prompt)` | Custom prompts that the built-ins don't cover | depends on endpoint |

Prefer the built-ins (`ai_analyze_sentiment`, `ai_classify`, `ai_extract`, `ai_summarize`) over `ai_query` -- they are cheaper, governed, and don't require a serving endpoint.

## Standard Output Schema

Every Silver-layer sentiment table MUST expose at least these columns, in this order, before the standard `data_quality_flag` and audit columns:

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| `<entity>_id` | identifier | source | Primary key from the source row (e.g. `review_id`) |
| `source_text` | STRING | source | Raw text fed to the AI functions (kept for debugging / re-runs) |
| `sentiment_label` | STRING | `ai_analyze_sentiment` | One of `positive`, `negative`, `neutral`, `mixed` |
| `topic_label` | STRING | `ai_classify` | From a project-defined topic taxonomy |
| `extracted_entities` | STRUCT | `ai_extract` | Named entities (product, person, location, etc.) |
| `summary` | STRING | `ai_summarize` (optional) | Short summary, only when source text is long |

If you add additional AI-derived columns, name them with the prefix `ai_` (e.g. `ai_intent`) so they are easy to audit and drop in downstream filtering.

## Bronze -- Pass Text Through Untouched

Bronze tables MUST NOT call AI functions. AI calls cost money and bronze is a raw replay layer. Bronze for an AI pipeline simply lands the text plus stable identifiers.

```sql
CREATE OR REFRESH STREAMING TABLE bronze_reviews
COMMENT "Raw customer reviews ingested from <catalog>.<bakehouse_schema>.customer_reviews"
TBLPROPERTIES (
  "quality" = "bronze",
  "owner" = "dsml",
  "domain" = "customer_voice"
)
CLUSTER BY AUTO
AS SELECT
  review_id,
  customer_id,
  franchise_id,
  product_id,
  review_text,
  review_date,
  current_timestamp() AS audit_timestamp,
  'bakehouse_marketplace' AS source_system
FROM STREAM(<catalog>.<bakehouse_schema>.customer_reviews)
WHERE review_id IS NOT NULL
  AND review_text IS NOT NULL;
```

## Silver -- Apply AI Functions

Silver is where AI functions run. Use a `MATERIALIZED VIEW` so the AI calls execute only on refresh, not per query. Always:

1. Filter junk text (NULL, very short, whitespace) BEFORE calling AI functions -- avoids paying for noise and pollutes label distributions.
2. Wrap each AI call in a `CASE` so empty input does not invoke the function.
3. Add a `data_quality_flag` describing AI failure modes (`MISSING_TEXT`, `AI_NULL_RESPONSE`, `CLEAN`).

```sql
CREATE OR REFRESH MATERIALIZED VIEW silver_review_sentiment(
  CONSTRAINT valid_review_id EXPECT (review_id IS NOT NULL) ON VIOLATION FAIL UPDATE,
  CONSTRAINT valid_sentiment EXPECT (sentiment_label IN ('positive','negative','neutral','mixed') OR sentiment_label IS NULL) ON VIOLATION DROP ROW
)
COMMENT "Customer reviews with AI-derived sentiment, topic and entities from bronze_reviews"
TBLPROPERTIES (
  "quality" = "silver",
  "owner" = "dsml",
  "domain" = "customer_voice",
  "delta.enableChangeDataFeed" = "true",
  "delta.enableRowTracking" = "true"
)
AS SELECT
  review_id,
  customer_id,
  franchise_id,
  product_id,
  review_text AS source_text,
  CASE
    WHEN LENGTH(TRIM(review_text)) < 5 THEN NULL
    ELSE ai_analyze_sentiment(review_text)
  END AS sentiment_label,
  CASE
    WHEN LENGTH(TRIM(review_text)) < 5 THEN NULL
    ELSE ai_classify(
      review_text,
      ARRAY('product_quality', 'service', 'price', 'ambiance', 'other')
    )
  END AS topic_label,
  CASE
    WHEN LENGTH(TRIM(review_text)) < 5 THEN NULL
    ELSE ai_extract(review_text, ARRAY('product_name', 'staff_name'))
  END AS extracted_entities,
  CASE
    WHEN review_text IS NULL OR LENGTH(TRIM(review_text)) < 5 THEN 'MISSING_TEXT'
    WHEN ai_analyze_sentiment(review_text) IS NULL THEN 'AI_NULL_RESPONSE'
    ELSE 'CLEAN'
  END AS data_quality_flag,
  current_timestamp() AS audit_timestamp,
  'bakehouse_marketplace' AS source_system
FROM LIVE.bronze_reviews;

ALTER TABLE silver_review_sentiment
  ALTER COLUMN review_id COMMENT 'Unique review identifier from bakehouse.media.customer_reviews',
  ALTER COLUMN source_text COMMENT 'Raw review text passed to the AI functions; retained for audit and re-runs',
  ALTER COLUMN sentiment_label COMMENT 'Output of ai_analyze_sentiment: positive | negative | neutral | mixed',
  ALTER COLUMN topic_label COMMENT 'Output of ai_classify against the customer-voice taxonomy',
  ALTER COLUMN extracted_entities COMMENT 'Output of ai_extract: STRUCT<product_name:STRING, staff_name:STRING>',
  ALTER COLUMN data_quality_flag COMMENT 'Row-level DQ status: CLEAN | MISSING_TEXT | AI_NULL_RESPONSE';

ALTER TABLE silver_review_sentiment
  SET TAGS ('quality' = 'silver', 'domain' = 'customer_voice', 'data_classification' = 'internal', 'ai_generated' = 'true');
```

## Gold -- Aggregate Sentiment Signals

Gold tables MUST NOT call AI functions and MUST NOT contain `source_text`. They aggregate sentiment by business dimensions for dashboards.

```sql
CREATE OR REFRESH MATERIALIZED VIEW gold_review_sentiment_by_franchise
COMMENT "Sentiment distribution by franchise and topic, sourced from silver_review_sentiment"
TBLPROPERTIES (
  "quality" = "gold",
  "owner" = "dsml",
  "domain" = "customer_voice",
  "delta.enableChangeDataFeed" = "true"
)
AS SELECT
  f.franchise_id,
  f.name AS franchise_name,
  s.topic_label,
  s.sentiment_label,
  COUNT(*) AS review_count,
  ROUND(
    COUNT_IF(s.sentiment_label = 'positive') * 100.0 / NULLIF(COUNT(*), 0),
    1
  ) AS positive_pct,
  ROUND(
    COUNT_IF(s.sentiment_label = 'negative') * 100.0 / NULLIF(COUNT(*), 0),
    1
  ) AS negative_pct,
  current_timestamp() AS audit_timestamp,
  'gold_aggregation' AS source_system
FROM LIVE.silver_review_sentiment s
JOIN <catalog>.<bakehouse_schema>.franchises f
  ON s.franchise_id = f.franchise_id
WHERE s.data_quality_flag = 'CLEAN'
GROUP BY f.franchise_id, f.name, s.topic_label, s.sentiment_label;
```

## Cost and Quality Guardrails

AI functions are billed per call and per token. Apply ALL of the following:

- **Pre-filter junk text.** Always gate AI calls behind a `LENGTH(TRIM(text)) >= 5` (or domain-appropriate minimum) check.
- **Materialize, don't view.** Use `MATERIALIZED VIEW`, not `VIEW`, so AI calls run once per refresh, not per query.
- **Cap the dev volume.** During development, add a deterministic `WHERE MOD(HASH(review_id), 100) = 0` sample so iteration runs over ~1% of rows. Remove before production.
- **Stable inputs.** Pass the raw column directly, not a non-deterministic expression. AI outputs change with input phrasing.
- **Reuse outputs.** Downstream tables should consume the silver AI columns -- never re-call the AI function in gold.
- **CDC for downstream.** Set `delta.enableChangeDataFeed = "true"` on silver/gold so consumers can incrementally pick up new sentiment without rerunning AI.

## Quality Constraints for AI Outputs

Add `CONSTRAINT` clauses to silver tables to guard against drift in AI label values:

```sql
CONSTRAINT valid_sentiment EXPECT (
  sentiment_label IN ('positive','negative','neutral','mixed')
  OR sentiment_label IS NULL
) ON VIOLATION DROP ROW,
CONSTRAINT valid_topic EXPECT (
  topic_label IN ('product_quality','service','price','ambiance','other')
  OR topic_label IS NULL
) ON VIOLATION DROP ROW
```

If a constraint trips frequently, the AI label set has drifted -- don't widen the constraint silently. Update the taxonomy in code review.

## PII Considerations

Customer reviews routinely contain names, emails, phone numbers, and order IDs that count as PII. Follow `@pii-management`:

- Annotate `source_text` as `-- [PII: FREEFORM - HIGH]`.
- Do NOT propagate `source_text` to gold.
- Do NOT join silver sentiment to PII-bearing customer attributes in gold; aggregate first.
- If `extracted_entities.staff_name` is a real employee name, mask or hash it before exposing externally.

## Worked Example: Bakehouse Customer Reviews

The `@sentiment-analysis` skill is demoed end-to-end against the **AI/BI Bakehouse** Marketplace share. The install notebook ([`marketplace_data/install_bakehouse.py`](../../marketplace_data/install_bakehouse.py)) lands the share in a scratch catalog and then mirrors the relevant tables into `<catalog>.<bakehouse_schema>` so the demo lives under a single, predictable namespace:

| Source table | Used for |
|--------------|----------|
| `<catalog>.<bakehouse_schema>.customer_reviews` | Bronze -- raw review text + stable IDs |
| `<catalog>.<bakehouse_schema>.franchises` | Gold -- enrich aggregates with `franchise_name` |
| `<catalog>.<bakehouse_schema>.transactions` | Gold (optional) -- join basket value to sentiment for revenue-impact views |

Recommended Genie Code prompt to drive the full pipeline (substitute your catalog and schema, e.g. `genie_code_skills_demo.bakehouse`):

> Build a bronze, silver, and gold pipeline from `<catalog>.<bakehouse_schema>.customer_reviews`. Add sentiment, topic, and extracted entities on silver using AI functions, then aggregate sentiment by franchise on gold. Apply `@table-governance`, `@sdp-basics`, `@pii-management`, and `@sentiment-analysis`.

## Sentiment-Analysis Checklist

Before completing any sentiment table, verify ALL of the following:

- [ ] Bronze contains raw text only -- no AI calls
- [ ] Silver uses `MATERIALIZED VIEW` (not `VIEW`)
- [ ] AI calls are gated behind a non-empty / minimum-length filter
- [ ] Output columns include `sentiment_label`, `topic_label`, `extracted_entities` as appropriate
- [ ] `CONSTRAINT` clauses pin sentiment / topic to a known label set
- [ ] `data_quality_flag` distinguishes `MISSING_TEXT` vs `AI_NULL_RESPONSE` vs `CLEAN`
- [ ] `delta.enableChangeDataFeed` set on silver/gold
- [ ] `audit_timestamp` and `source_system` are the LAST columns
- [ ] PII guidance from `@pii-management` is applied to `source_text` and `extracted_entities`
- [ ] Gold contains aggregates only -- no `source_text`, no AI calls
