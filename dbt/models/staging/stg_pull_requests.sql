WITH raw_pull_requests AS (
    SELECT * FROM {{ source('github_data', 'pull_requests') }}
)

SELECT
    id AS pr_id,
    number AS pr_number,
    title,
    state,
    created_at::TIMESTAMP AS created_at,
    updated_at::TIMESTAMP AS updated_at,
    closed_at::TIMESTAMP AS closed_at,
    merged_at::TIMESTAMP AS merged_at,
    user__id AS user_id,
    user__login AS user_login
FROM raw_pull_requests
