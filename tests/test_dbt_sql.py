import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'src'))
from certiflow.dbt_sql import normalize_dbt_model,preprocess_dbt_sql

def test_preprocess_ref_source_and_opaque_macro():
    out,n=preprocess_dbt_sql("select {{ cents_to_dollars('price') }} as price from {{ ref('products') }}");assert 'products' in out and 'DBT_EXPR_1()' in out and n==1

def test_cte_staging_model_normalization():
    sql="with source as (select * from {{ source('ecom','raw_customers') }}), renamed as (select id as customer_id, name as customer_name from source) select * from renamed";r=normalize_dbt_model(sql,model_name='stg_customers');assert r.ctes==('source','renamed');assert 'ecom__raw_customers' in r.graph.nodes;assert r.graph.nodes['stg_customers__cte__source'].op=='Alias';assert r.graph.nodes['stg_customers__cte__renamed'].op=='Project';assert r.graph.nodes['stg_customers'].op=='Alias'

def test_dbt_computed_expression_is_preserved_not_certified_as_mapping():
    sql="with source as (select * from raw_products), renamed as (select sku as product_id, {{ cents_to_dollars('price') }} as price from source) select * from renamed";r=normalize_dbt_model(sql,model_name='products');project=r.graph.nodes['products__cte__renamed'];assert project.args['mapping']['product_id']=='sku';assert 'price' in project.args['computed'];assert r.opaque_expressions==1

def test_relation_generating_macro_becomes_opaque_boundary():
    r=normalize_dbt_model("with days as ({{ dbt.date_spine('day','a','b') }}), final as (select date_day from days) select * from final",model_name='spine');assert r.opaque_relations==1;assert r.graph.nodes['spine__cte__days'].op=='Opaque'
