# Python Client

This project contains Python applications and Flink SQL statements for populating and analyzing topic information across a number of data systems listening to said topic.

## Getting Started

### Prerequisites
- Python 3 (tested with 3.12.2)
- virtualenv (or similar, like `venv`)
- confluent CLI

### Installation

Create and activate a Python environment, so that you have an isolated workspace:

```shell
virtualenv env
source env/bin/activate
```

Install the dependencies of this application:

```shell
pip install -r requirements.txt
```

Make the scripts executable:

```shell
chmod u+x producer.py tableflow.py
```

Ensure the confluent cli is installed to the latest version (v4.45.1 as of this page being written). Use [confluent-cli install](https://docs.confluent.io/confluent-cli/current/install.html) instructions based on your operating system.

### Configuration
Set environment variables in `.env` -- there's more than prior projects because of the number of systems we are using:
- `CC_TOPIC` -- The topic name we're using (`sales_orders` in live example)
- `CC_API_KEY` -- Kafka producer API key
- `CC_API_SECRET` -- Kafka producer API secret
- `CC_BOOTSTRAP_SERVER` -- Kafka server URI
- `CC_API_BASE_URL`
- `CC_SR_API_KEY` -- Kafka producer Schema Registry key
- `CC_SR_API_SECRET` -- Kafka producer Schema Registry key
- `CC_SCHEMA_REGISTRY_URL`
- `CC_TABLEFLOW_API_KEY` -- Tableflow API key separate from Kafka
- `CC_TABLEFLOW_API_SECRET` -- Tableflow API secret separate from Kafka
- `CC_ORG_ID` -- Makes the scripting more general, not needed if you want to hardcode
- `CC_REGION` -- Makes the scripting more general, not needed if you want to hardcode
- `CC_ENV_ID` -- Makes the scripting more general, not needed if you want to hardcode
- `CC_KAFKA_CLUSTER` -- Makes the scripting more general, not needed if you want to hardcode

### Producer Usage

You can execute the producer script by running:

```shell
./producer.py
```

Unlike in the prior steps, this script is modified to repeat data forever with increasing ids to better emulate live data streams.

Once you are done with the walkthrough, enter `ctrl+C` to terminate the producer application.

### Docker

Make sure you have your [Docker desktop app](https://www.docker.com/products/docker-desktop/) installed and running.

From the root directory of the generated project, run:

```
docker compose build --no-cache
docker compose up
```

## Flink

Next we'll explore the flink options for real-time processing in more depth. The queries listed below have cooresponding `.flink.sql` extension files for running the completed code.

### Querying Data with Flink

- Create a new file by selecting `File`, `New File...`.
- Change the language mode to `Flink SQL`, by selecting the `select a language` watermark, or `Plain text` on the status bar.
- Select `Set compute pool`, then select the Flink compute pool you created in step 0.
- Select `Set catalog & database`, then select the environment and cluster you created in step 0.
- Enter a simple Flink SQL query to make sure it works.
  ```sql
  SELECT * FROM `sales_orders`;
  ```
- Submit the query.
- Use the query result viewer to confirm data is returned as expected.

### Aggregating Sales Orders

- Update your Flink SQL script to aggregate sales orders in a time window. We want to know the item IDs and total number of orders within each 1 minute interval.
  ```sql
  SELECT
      window_start,
      window_end,
      ARRAY_AGG(DISTINCT itemid) AS item_ids,
      COUNT(*) AS total_orders
  FROM TABLE (
      TUMBLE(TABLE sample_data, DESCRIPTOR(`$rowtime`), INTERVAL '10' SECOND)
  )
  GROUP BY window_start, window_end
    ```
- Submit the query.
- Review the results in the query result viewer.

### Enhancing the Query

- You're being asked to add a new column for the total order amount per time indow.
```sql
SELECT
    window_start,
    window_end,
    ARRAY_AGG(DISTINCT itemid) AS item_ids,
    COUNT(*) AS total_orders,
    SUM(orderAmount) AS total_amount
FROM TABLE (
    TUMBLE(TABLE sample_data, DESCRIPTOR(`$rowtime`), INTERVAL '10' SECOND)
)
GROUP BY window_start, window_end
```
- Confirm the new column appears and values are as expected.

### Make It Into a Persistent Query

- Now that we know the query is working as expected, we can turn it into a presistent query that runs in the background.
- Modify the query and change it from `SELECT` to `CREATE OR INSERT`
```sql
CREATE TABLE processed_orders AS
SELECT
    window_start,
    window_end,
    ARRAY_AGG(DISTINCT itemid) AS item_ids,
    COUNT(*) AS total_orders,
    SUM(orderAmount) AS total_amount
FROM TABLE (
    TUMBLE(TABLE sample_data, DESCRIPTOR(`$rowtime`), INTERVAL '10' SECOND)
)
GROUP BY window_start, window_end
```
- Submit the query, and confirm the table is created and contains the data as expected.

## Tableflow

First we need to turn on tableflow for our topic. Below we'll use the confluent CLI to activate a topic as an Iceberg table. Later we'll then read this table from DuckDB, though you could use a batch tool of your choice at that stage.

Notes: Some regions / cloud providers haven't reached GA service availability here for Tableflow as of Dec 1st 2025, so we'll use AWS us-east-2 in our example. But this constraint will go away shortly here after.

### Registration

You can enable these Tableflow actions from the CCloud UI as well: simply go to your topic page within your cluster and click the button that says "Enable Tableflow". It will guide you through answering the questions below if you select Confluent storage to turn on sync to Iceberg.

But we can also just do these actions from the command line as follows.

```bash
# Load in our environment variables
set -a; source .env; set+a

confluent login
confluent environment use $CC_ENV_ID
confluent kafka cluster use $CC_KAFKA_CLUSTER
confluent api-key store $CC_API_KEY $CC_API_SECRET
confluent api-key use $CC_API_KEY --resource $CC_KAFKA_CLUSTER

# Enable Tableflow for the $CC_TOPIC
confluent tableflow topic enable $CC_TOPIC \
  --cluster $CC_KAFKA_CLUSTER \
  --storage-type MANAGED \
  --table-formats ICEBERG \
  --retention-ms 604800000

# Monitor materialization progress
confluent tableflow topic describe $CC_TOPIC --cluster $CC_KAFKA_CLUSTER

# Wait for initial data to be materialized (2-3 minutes)
confluent tableflow topic list --cluster $CC_KAFKA_CLUSTER
```

### Local Connection with DuckDB

For this query pattern we'll use the DuckDB dependency installed via the Python dependencies, though you could run any of these SQL commands you'll see from any DuckDB interface. We use Python here for consistency with the earlier steps.

First we load launch a `python` cli prompt then we use that to load our environment. Make sure you start python within the directory where we have the `.env` with our secret variables.

```python
import os
import duckdb
from dotenv import load_dotenv

load_dotenv()
org_id = os.getenv("CC_ORG_ID")
region = os.getenv("CC_REGION", "us-east-2")
env_id = os.getenv("CC_ENV_ID")
cluster_id = os.getenv("CC_KAFKA_CLUSTER")
topic = os.getenv("CC_TOPIC")
tableflow_key = os.getenv("CC_TABLEFLOW_API_KEY")
tableflow_secret = os.getenv("CC_TABLEFLOW_API_SECRET")
```

Now we create our tableflow secret that allows access to the blob storage where our tableflow files exist.

```python
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
```

Then we need to create a local database connected using that secret.

```python
duckdb.sql(f"""
    ATTACH 'warehouse' AS iceberg_catalog (
    TYPE iceberg,
    SECRET iceberg_secret,
    ENDPOINT 'https://tableflow.{region}.aws.confluent.cloud/iceberg/catalog/organizations/{org_id}/environments/{env_id}'
);
""")
```

Let's validate this connection has successfully created a virtual `sales_order` table locally.

```python
duckdb.sql("SHOW DATABASES;").show()
duckdb.sql(f'SHOW TABLES FROM iceberg_catalog;').show()
duckdb.sql(f'DESCRIBE iceberg_catalog."{cluster_id}"."{topic}";').show()
```

You should now see databases and our Kafka table under the new iceberg catalog we created.

Finally we need should test that we can run SQL statements against the this table.

```python
duckdb.sql(f'SELECT * FROM iceberg_catalog."{cluster_id}"."sales_orders" LIMIT 10;').show()
```

And viola! We can now run any batch queries against the same topic that we also have our realtime systems querying without needing to write any custom consumers or connectors.

## Troubleshooting

### Package Installation

If `pip install` fails with librdkafka error, check Python version compatibility.

For more details, check the [Confluent Cloud documentation](https://docs.confluent.io/cloud/current/overview.html).

### Can't Environment Variables

Make sure you are in the same working directory as your `.env` file when loading a python prompt or program. You can test that the file is correct by doing `set -a; source .env; set +a; echo $CC_TOPIC`. If you see your topic name print it's setup correctly.
