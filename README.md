# Confluent for VS Code Extension Workshop

## Overview

Welcome to the Confluent for VS Code Extension Workshop! In this hands-on session, you'll simulate building a real-time data pipeline using Apache Kafka and Flink, all from within your IDE.

You are a developer at **Llama Electronics**, a quirky yet fast-growing electronic goods retailer, who’s tasked with integrating and processing e-commerce data for downstream analysis. By the end of this workshop, you’ll know how to:

- Generate and run Kafka applications using VS Code
- Simulate data pipelines without production access
- Author and run Flink SQL queries locally
- Use GitHub Copilot to accelerate development

---
## Prerequisites

Before you begin, please make sure you have the following installed and configured:

- **[Confluent Cloud Account](https://confluent.cloud/signup)**  
  You can use any Kafka cluster to complete the first two steps of the workshop. But Confluent Cloud and Confluent Cloud for Apache Flink is required to continue later steps.

- **[Visual Studio Code](https://code.visualstudio.com/)**  
  Your development environment for this workshop.

- **[Confluent for VS Code Extension](https://marketplace.visualstudio.com/items?itemName=confluentinc.vscode-confluent)**  
  Install from the VS Code Marketplace.

- **[Docker Desktop](https://www.docker.com/products/docker-desktop)** *(Optional)*  
  Needed only if you prefer to run Kafka locally while debugging.

---

## Scenario

You're tasked with building a near real-time reporting system for Llama Electronics. Sales data comes from Salesforce, but direct access is restricted. you only has a sample JSON dataset to work with. Luckily, with the Confluent for VS Code Extension and GitHub Copilot, you can simulate the pipeline locally and prepare everything before production is live.

---

### Workshop Steps

### 0. Setup

1. If you don't have a Confluent Cloud account, sign up [here](https://confluent.cloud/signup).
1. Create a new environment ([doc](https://docs.confluent.io/cloud/current/security/access-control/hierarchy/cloud-environments.html#add-an-environment))
1. Create a new Kafka cluster ([doc](https://docs.confluent.io/cloud/current/clusters/create-cluster.html#create-ak-clusters)).
1. Create a new API key for the Kafka cluster, make sure to save it for use later ([doc](https://docs.confluent.io/cloud/current/security/authenticate/workload-identities/service-accounts/api-keys/manage-api-keys.html#add-an-api-key)).
1. Create a new API key for Schema Registry, make sure to save it for use later ([doc](https://docs.confluent.io/cloud/current/security/authenticate/workload-identities/service-accounts/api-keys/manage-api-keys.html#add-an-api-key)).
1. Create a new Flink compute pool ([doc](https://docs.confluent.io/cloud/current/flink/operate-and-deploy/create-compute-pool.html#create-a-compute-pool)).


### 1. Connect to Confluent Cloud

1. Navigate to the Confluent tab in VS Code.
1. Click on the "Sign in" icon next to Confluent Cloud and sign in.

> [!TIP]
> If you cannot sign up for Confluent Cloud, or prefer debugging your code against a local Kafka cluster first, you can start a local Kafka cluster using the extension instead. 

### 2. Create a Kafka Producer Project

You can scaffold a producer project in multiple ways.

#### Option A: Command Palette

1. In VS Code, open the Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`).
1. Type and select `Confluent: Generate Project`.

#### Option B: Extension Sidebar

1. Open the Confluent sidebar in VS Code.
1. Scroll to **Support** > **Generate Project from Template**.
1. Follow the prompts to scaffold the project.

#### Set Up and Run the Project
1. Choose a Kafka producer template in the language of your preference (e.g., Python).
1. Enter `Kafka Bootstrap Server`, `Kafka Cluster API Key`, `Kafka Cluster API Secret`, and `Topic Name`, `Schema Registry URL`, `Schema Registry API Key`, and `Schema Registry API Secret`, then select `Generate & Save`.
   1. To create an API Key and Secret for the cluster, navigate to the cluster overview page, API Keys, Add Key, and follow the on screen instruction to create one.
   1. To create an API Key and Secret for Schema Registry, navigate to the Stream Governance, Schema Registry, API Keys, Add Key, and follow the on screen instruction to create one.
   1. We will call the topic name `sales_orders`.
1. Set your project name and destination folder.
1. Open the generated folder in VS Code.
Follow the instructions in the `README.md` file of the generated project if you've selected a language other than Python.
1. Create a Python virtual environment:
    ```bash
    virtualenv env
    source env/bin/activate
    ```
1. Install the dependencies of this application:
    ```shell
    pip install -r requirements.txt
    ```
1. Make the scripts executable:
    ```shell
    chmod u+x producer.py consumer.py
    ```
1. You can execute the producer script by running:
    ```shell
    ./producer.py
    ```
1. You will see error in the console output about topic doesn't exist, to fix this, create a new topic with name `sales_orders`.
1. Re-run the producer script to confirm it's now working.

#### Verify messages are produced:
  - Go to the Confluent extension tab in the sidebar.
  - Select the environment and cluster you used when generating the project.
  - Locate the topic you're producing to while configuring the project, and click on the icon to view messages.
  - Confirm the 10 sample messages are produced to the topic.

> [!TIP]
> Can’t get the project working? You can find pre-generated projects in the `1-project-setup` folder. Go to the folder for your preferred language, and continue with step 2 of the workshop.


### 3. Customizing the Producer
Let’s update producer so that it produces messages based on the sample data provided.

- Locate the producer code file (e.g., `producer.py`) from your project folder.
- Download and copy `sample_data.json` into project's root folder.
- Toggle on GitHub Copilot chat window.
- Make sure you are in **Agent** or **Edit** mode.
  - Copilot should automatically select the currently opened file, e.g. `producer.py` as context.
  - Select "Add Context...", and choose the `sample_data.json` file in the same folder to include it as additional context.
- Use Copilot to rewrite the logic so it reads from the JSON file and produces records that match the sample data format.
    - Prompt Copilot to update the code and use content of `sample_data.json` to generate messages.

> [!NOTE]
> Suggested prompt: Update `producer.py`, instead of generating hardcoded messages, read the content in `sample_data.json`, generate and send messages based on its content. update `sample-schema.avsc` to match the new data.

- Review Copilot's suggestions and accept or refine as needed.
- Save your changes to `producer.py`.
- Before running the producer code, delete `sales_orders` topic and `sales_orders-value` schema created previously.
- Run the producer code again and confirm that it now reads from the CSV and produces the correct records.
  ```shell
  ./producer.py
  ```
- In the Confluent for VSCode extension sidebar, find your Kafka cluster and topic.
- Right-click the topic and select "View Messages".
- Confirm that the produced messages match the sample data.

> [!TIP]
> If you have trouble updating the project code using copilot, you can find pre-generated projects in the `2-project-modify` folder. Go to the folder for your preferred language and use it to proceed with the workshop.


### 4. Querying Data with Flink

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

### 5. Aggregating Sales Orders

- Update your Flink SQL script to aggregate sales orders in a time window. We want to know the item IDs and total number of orders within each 1 minute interval.
  ```sql
  SELECT
      window_start,
      window_end,
      ARRAY_AGG(DISTINCT itemid) AS item_ids,
      COUNT(*) AS total_orders
  FROM TABLE (
      TUMBLE(TABLE sample_data, DESCRIPTOR(`$rowtime`), INTERVAL '1' SECOND)
  )
  GROUP BY window_start, window_end
    ```
- Submit the query.
- Review the results in the query result viewer.

### 6. Enhancing the Query

- You're being asked to add a new column for the total order amount per time indow.
- Let's use GitHub Copilot to modify the query.
> [!NOTE]
> Suggested prompt: Update the query to include a new column, `total_amount`, that will calculate the sum of all orders within the time window.
```sql
SELECT
    window_start,
    window_end,
    ARRAY_AGG(DISTINCT itemid) AS item_ids,
    COUNT(*) AS total_orders,
    SUM(orderAmount) AS total_amount
FROM TABLE (
    TUMBLE(TABLE sample_data, DESCRIPTOR(`$rowtime`), INTERVAL '1' SECOND)
)
GROUP BY window_start, window_end
```
- Review Copilot suggestion, accept if correct, and resubmit the query.
- Confirm the new column appears and values are as expected.

### 7. Make It Into a Persistent Query

- Now that we know the query is working as expected, we can turn it into a presistent query that runs in the background.
- Modify the query and change it from `SELECT` to `CREATE OR INSERT`
> [!NOTE]
> Suggested prompt: Update the query to  presistent query and write the output to table named `processed_orders`
```sql
CREATE TABLE processed_orders AS
SELECT
    window_start,
    window_end,
    ARRAY_AGG(DISTINCT itemid) AS item_ids,
    COUNT(*) AS total_orders,
    SUM(orderAmount) AS total_amount
FROM TABLE (
    TUMBLE(TABLE sample_data, DESCRIPTOR(`$rowtime`), INTERVAL '1' SECOND)
)
GROUP BY window_start, window_end
```
- Review Copilot suggestion, accept if correct, and resubmit the query.
- Submit the query, and confirm the table is created and contains the data as expected.


---

## Next Steps

- Make sure to enable Auto Update for the extension to receive the latest improvements.
- Add a connector to produce data from an external systems.
- Use [Mockstream](https://mockstream.confluent.io/) to produce more sophisticated mock data. 
- Create a Kafka consumer app from project template to consume the processed data after Flink SQL.