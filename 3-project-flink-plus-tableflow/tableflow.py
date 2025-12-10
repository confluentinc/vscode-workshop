import os
import duckdb
from dotenv import load_dotenv

if __name__ == "__main__":
    '''
    Setup DuckDB with Tableflow integration, then run a simple query to show that we can now read
    from the Iceberg tables in any Iceberg compatible system.
    '''
    load_dotenv()

    org_id = os.getenv("CC_ORG_ID")
    region = os.getenv("CC_REGION", "us-east-2")
    env_id = os.getenv("CC_ENV_ID")
    cluster_id = os.getenv("CC_KAFKA_CLUSTER")
    tableflow_key = os.getenv("CC_TABLEFLOW_API_KEY")
    tableflow_secret = os.getenv("CC_TABLEFLOW_API_SECRET")

    print("Setting up Tableflow secret in DuckDB...")

    # Register our secret in DuckDB
    duckdb.sql(f"""
        CREATE SECRET iceberg_secret (
        TYPE ICEBERG,
        CLIENT_ID '{tableflow_key}',
        CLIENT_SECRET '{tableflow_secret}',
        ENDPOINT 'https://tableflow.{region}.aws.confluent.cloud/iceberg/catalog/organizations/{org_id}/environments/{env_id}',
        OAUTH2_SCOPE 'catalog'
    );
    """)

    duckdb.sql(f"""
        ATTACH 'warehouse' AS iceberg_catalog (
        TYPE iceberg,
        SECRET iceberg_secret,
        ENDPOINT 'https://tableflow.{region}.aws.confluent.cloud/iceberg/catalog/organizations/{org_id}/environments/{env_id}'
    );
    """)


    print("Running DuckDB with Tableflow...")
    duckdb.sql("SHOW DATABASES;").show()
    duckdb.sql(f'SHOW TABLES FROM iceberg_catalog;').show()
    duckdb.sql(f'DESCRIBE iceberg_catalog."{cluster_id}"."sales_orders";').show()

    duckdb.sql(f'SELECT * FROM iceberg_catalog."{cluster_id}"."sales_orders" LIMIT 10;').show()
    print("Done.")