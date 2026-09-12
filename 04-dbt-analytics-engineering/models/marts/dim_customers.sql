-- dim_customers: satu baris per customer, diperkaya dengan status subscription
-- terkininya. Ini pola umum "current-state dimension" di dimensional modeling.

with customers as (
    select * from {{ ref('stg_customers') }}
),

subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

-- Ambil subscription TERBARU per customer (berdasarkan start_date),
-- supaya customer yang pernah churn lalu subscribe lagi tetap kebaca statusnya
-- yang paling akhir, bukan yang pertama.
latest_subscription as (
    select
        customer_id,
        plan_type,
        status,
        start_date,
        end_date,
        monthly_price_usd,
        row_number() over (
            partition by customer_id
            order by start_date desc
        ) as rn
    from subscriptions
)

select
    c.customer_id,
    c.customer_name,
    c.email,
    c.signup_date,
    c.country,
    ls.plan_type          as current_plan_type,
    ls.status              as current_subscription_status,
    ls.monthly_price_usd   as current_monthly_price_usd,
    (ls.status = 'active') as is_active_subscriber
from customers c
left join latest_subscription ls
    on c.customer_id = ls.customer_id
    and ls.rn = 1
