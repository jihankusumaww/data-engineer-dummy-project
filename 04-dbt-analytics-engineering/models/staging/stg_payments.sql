with source as (
    select * from {{ ref('raw_payments') }}
)

select
    payment_id::integer                        as payment_id,
    subscription_id::integer                    as subscription_id,
    payment_date::date                          as payment_date,
    {{ cents_to_dollars('amount_cents') }}      as amount_usd,
    status                                       as payment_status
from source
