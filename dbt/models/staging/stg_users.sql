WITH pr_users AS (
    SELECT
        (raw_data -> 'user' ->> 'id')::BIGINT AS user_id,
        raw_data -> 'user' ->> 'login' AS user_login
    FROM raw.pull_requests
    WHERE raw_data -> 'user' IS NOT NULL
),

issue_users AS (
    SELECT
        (raw_data -> 'user' ->> 'id')::BIGINT AS user_id,
        raw_data -> 'user' ->> 'login' AS user_login
    FROM raw.issues
    WHERE raw_data -> 'user' IS NOT NULL
)

SELECT DISTINCT
    user_id,
    user_login
FROM (
    SELECT
        pr_users.user_id,
        pr_users.user_login
    FROM pr_users
    UNION ALL
    SELECT
        issue_users.user_id,
        issue_users.user_login
    FROM issue_users
) AS u
WHERE user_id IS NOT NULL
