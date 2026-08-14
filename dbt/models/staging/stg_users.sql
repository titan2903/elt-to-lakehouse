WITH pr_users AS (
    SELECT
        user__id AS user_id,
        user__login AS user_login
    FROM {{ source('github_data', 'pull_requests') }}
    WHERE user__id IS NOT NULL
),

issue_users AS (
    SELECT
        user__id AS user_id,
        user__login AS user_login
    FROM {{ source('github_data', 'issues') }}
    WHERE user__id IS NOT NULL
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
