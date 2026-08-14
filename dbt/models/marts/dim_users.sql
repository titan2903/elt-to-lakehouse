WITH staging AS (
    SELECT * FROM {{ ref('stg_users') }}
)

SELECT
    user_id,
    user_login
FROM staging
