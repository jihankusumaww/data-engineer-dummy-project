-- fct_mrr: Monthly Recurring Revenue per plan per bulan.
-- Ini pola "date spine" yang umum di analytics engineering: kita generate
-- semua bulan dari awal data sampai sekarang, lalu untuk tiap bulan hitung
-- subscription mana saja yang aktif di bulan itu. Tanpa date spine, bulan
-- yang tidak punya event baru (misal tidak ada subscription baru) akan
-- "hilang" dari hasil agregasi biasa -- padahal MRR bulan itu tetap ada
-- dari subscription yang sudah berjalan sebelumnya.

with months as (
    select unnest(generate_series(
        (select date_trunc('month', min(start_date)) from {{ ref('stg_subscriptions') }}),
        date_trunc('month', current_date),
        interval '1 month'
    )) as month_start
),

subscriptions as (
    select * from {{ ref('stg_subscriptions') }}
),

-- Subscription dianggap aktif di suatu bulan kalau bulan itu berada di
-- antara start_date dan end_date (atau belum churn sama sekali).
active_per_month as (
    select
        m.month_start,
        s.subscription_id,
        s.plan_type,
        s.monthly_price_usd
    from months m
    join subscriptions s
        on date_trunc('month', s.start_date) <= m.month_start
        and (s.end_date is null or date_trunc('month', s.end_date) >= m.month_start)
)

select
    month_start,
    plan_type,
    count(distinct subscription_id) as active_subscriptions,
    round(sum(monthly_price_usd), 2) as mrr_usd
from active_per_month
group by month_start, plan_type
order by month_start, plan_type
