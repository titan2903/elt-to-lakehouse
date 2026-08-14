WITH staging AS (
    SELECT * FROM {{ ref('stg_issues') }}
)

SELECT
    issue_id,
    issue_number,
    title,
    state,
    user_id,
    created_at,
    updated_at,
    closed_at,
    -- calculate duration in hours if closed
    CASE
        WHEN closed_at IS NOT NULL
            THEN (
                EXTRACT(EPOCH FROM (closed_at - created_at)) / 3600.0
            )::DOUBLE PRECISION
    END AS duration_hours
FROM staging
