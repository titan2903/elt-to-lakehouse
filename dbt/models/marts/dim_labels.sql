WITH flattened_labels AS (
    SELECT * FROM {{ source('github_data', 'issues__labels') }}
)

SELECT DISTINCT
    id AS label_id,
    name AS label_name
FROM flattened_labels
WHERE id IS NOT NULL
