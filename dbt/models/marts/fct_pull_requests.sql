WITH staging AS (
    SELECT * FROM {{ ref('stg_pull_requests') }}
)

SELECT
    pr_id,
    pr_number,
    title,
    state,
    user_id,
    created_at,
    updated_at,
    closed_at,
    merged_at,
    -- calculate duration in hours if merged
    CASE
        WHEN merged_at IS NOT NULL
            THEN
                EXTRACT(EPOCH FROM (merged_at - created_at)) / 3600.0
    END AS duration_hours
FROM staging
