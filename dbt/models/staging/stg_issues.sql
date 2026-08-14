WITH raw_issues AS (
    SELECT * FROM {{ source('github_data', 'issues') }}
)

SELECT
    id AS issue_id,
    number AS issue_number,
    title,
    state,
    created_at::TIMESTAMP AS created_at,
    updated_at::TIMESTAMP AS updated_at,
    closed_at::TIMESTAMP AS closed_at,
    user__id AS user_id,
    user__login AS user_login
FROM raw_issues
