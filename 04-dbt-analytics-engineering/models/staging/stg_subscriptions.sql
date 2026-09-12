with source as (
    select * from {{ ref('raw_subscriptions') }}
)

select
    subscription_id::integer                      as subscription_id,
    customer_id::integer                           as customer_id,
    plan_type                                       as plan_type,
    start_date::date                                as start_date,
    nullif(end_date, '')::date                      as end_date,
    {{ cents_to_dollars('monthly_price_cents') }}   as monthly_price_usd,
    status                                           as status
from source
