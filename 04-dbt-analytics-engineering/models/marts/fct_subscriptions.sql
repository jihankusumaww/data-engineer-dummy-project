-- fct_subscriptions: satu baris per subscription, diperkaya dengan durasi
-- dan total pembayaran yang berhasil (fact table di grain subscription).

with subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

payments as (
    select * from {{ ref('stg_payments') }}
),

payment_agg as (
    select
        subscription_id,
        sum(case when payment_status = 'success' then amount_usd else 0 end) as total_paid_usd,
        count(case when payment_status = 'success' then 1 end)                as successful_payments,
        count(case when payment_status = 'failed' then 1 end)                 as failed_payments
    from payments
    group by subscription_id
)

select
    s.subscription_id,
    s.customer_id,
    s.plan_type,
    s.status,
    s.start_date,
    s.end_date,
    s.monthly_price_usd,
    -- durasi dalam bulan: sampai end_date kalau sudah churn, atau sampai hari ini kalau masih aktif
    date_diff('month', s.start_date, coalesce(s.end_date, current_date)) as duration_months,
    coalesce(p.total_paid_usd, 0)        as total_paid_usd,
    coalesce(p.successful_payments, 0)   as successful_payments,
    coalesce(p.failed_payments, 0)       as failed_payments
from subscriptions s
left join payment_agg p on s.subscription_id = p.subscription_id
