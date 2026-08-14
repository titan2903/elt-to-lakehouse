WITH raw_issues AS (
    SELECT * FROM raw.issues
)

SELECT
    id AS issue_id,
    number AS issue_number,
    title,
    state,
    created_at,
    updated_at,
    (raw_data ->> 'closed_at')::TIMESTAMP AS closed_at,
    (raw_data -> 'user' ->> 'id')::BIGINT AS user_id,
    raw_data -> 'user' ->> 'login' AS user_login,
    raw_data -> 'labels' AS labels_json
FROM raw_issues
