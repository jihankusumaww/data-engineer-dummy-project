with source as (
    select * from {{ ref('raw_payments') }}
)

select
    payment_id::integer                        as payment_id,
    subscription_id::integer                    as subscription_id,
    try_cast(nullif(trim(payment_date), '') as date) as payment_date,
    {{ cents_to_dollars('amount_cents') }}      as amount_usd,
    status                                       as payment_status
from source
