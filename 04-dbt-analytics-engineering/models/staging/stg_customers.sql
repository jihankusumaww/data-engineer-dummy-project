-- Staging layer: 1:1 dengan source, cuma rename & cast type.
-- Prinsip: staging model TIDAK melakukan join atau agregasi bisnis,
-- itu tugas layer marts.

with source as (
    select * from {{ ref('raw_customers') }}
)

select
    customer_id::integer          as customer_id,
    trim(customer_name)           as customer_name,
    lower(trim(email))            as email,
    try_cast(nullif(trim(signup_date), '') as date) as signup_date,
    country                       as country
from source
