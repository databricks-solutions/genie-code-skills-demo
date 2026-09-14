# Sentiment pipeline templates

Reusable bronze / silver / gold SQL for `@sentiment-analysis`. Substitute catalog, schema, and source table names.

## Bronze -- raw text only (no AI calls)

```sql
CREATE OR REFRESH STREAMING TABLE bronze_reviews
COMMENT "Raw customer reviews ingested from <catalog>.<bakehouse_schema>.customer_reviews"
TBLPROPERTIES (
  "quality" = "bronze",
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

## Silver -- AI functions

```sql
CREATE OR REFRESH MATERIALIZED VIEW silver_review_sentiment(
  CONSTRAINT valid_review_id EXPECT (review_id IS NOT NULL) ON VIOLATION FAIL UPDATE,
  CONSTRAINT valid_sentiment EXPECT (sentiment_label IN ('positive','negative','neutral','mixed') OR sentiment_label IS NULL) ON VIOLATION DROP ROW,
  CONSTRAINT valid_topic EXPECT (
    topic_label IN ('product_quality','service','price','ambiance','other')
    OR topic_label IS NULL
  ) ON VIOLATION DROP ROW
)
COMMENT "Customer reviews with AI-derived sentiment, topic and entities from bronze_reviews"
TBLPROPERTIES (
  "quality" = "silver",
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
FROM bronze_reviews;

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

## Gold -- aggregates only (no source_text, no AI calls)

```sql
CREATE OR REFRESH MATERIALIZED VIEW gold_review_sentiment_by_franchise
COMMENT "Sentiment distribution by franchise and topic, sourced from silver_review_sentiment"
TBLPROPERTIES (
  "quality" = "gold",
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
FROM silver_review_sentiment s
JOIN <catalog>.<bakehouse_schema>.franchises f
  ON s.franchise_id = f.franchise_id
WHERE s.data_quality_flag = 'CLEAN'
GROUP BY f.franchise_id, f.name, s.topic_label, s.sentiment_label;
```
