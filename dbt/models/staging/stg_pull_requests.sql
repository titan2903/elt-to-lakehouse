WITH raw_pull_requests AS (
    SELECT * FROM raw.pull_requests
)

SELECT
    id AS pr_id,
    number AS pr_number,
    title,
    state,
    created_at,
    updated_at,
    (raw_data ->> 'closed_at')::TIMESTAMP AS closed_at,
    (raw_data ->> 'merged_at')::TIMESTAMP AS merged_at,
    (raw_data -> 'user' ->> 'id')::BIGINT AS user_id,
    raw_data -> 'user' ->> 'login' AS user_login
FROM raw_pull_requests
