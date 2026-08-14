WITH staging_issues AS (
    SELECT * FROM {{ ref('stg_issues') }}
),

-- Postgres JSON extraction to get individual labels
flattened_labels AS (
    SELECT
        issue_id,
        jsonb_array_elements(labels_json::jsonb) AS label_obj
    FROM staging_issues
    WHERE labels_json IS NOT NULL
),

extracted AS (
    SELECT
        (label_obj ->> 'id')::bigint AS label_id,
        label_obj ->> 'name' AS label_name
    FROM flattened_labels
)

SELECT DISTINCT
    label_id,
    label_name
FROM extracted
WHERE label_id IS NOT NULL
