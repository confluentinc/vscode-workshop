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
  Required to use Confluent Cloud for Apache Flink.

- **[Visual Studio Code](https://code.visualstudio.com/)**  
  Your development environment for this workshop.

- **[Confluent for VS Code Extension](vscode:extension/confluent.confluent)**  
  Install from the VS Code Marketplace.

- **[Docker Desktop](https://www.docker.com/products/docker-desktop)** *(Optional)*  
  Needed only if you prefer to run Kafka locally.

---

## Scenario

You're tasked with building a near real-time reporting system for Llama Electronics. Sales data comes from Salesforce, but direct access is restricted. you only has a sample JSON dataset to work with. Luckily, with the Confluent for VS Code Extension and GitHub Copilot, you can simulate the pipeline locally and prepare everything before production is live.

---

### Workshop Steps

### 1. Create a Kafka Producer Project

You can scaffold a producer project in multiple ways.

#### Option A: Command Palette

1. In VS Code, open the Command Palette (`Cmd+Shift+P` or `Ctrl+Shift+P`).
1. Type and select `Confluent: Generate Project`.
1. Choose a Kafka producer template (e.g., Python).
1. Set your project name and destination folder.
1. Open the generated folder in VS Code.

#### Option B: Extension Sidebar

1. Open the Confluent sidebar in VS Code.
2. Scroll to **Support** > **Generate Project from Template**.
3. Follow the prompts to scaffold the project.

#### Set Up and Run the Project

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

#### Verify messages are produced:**
  - Go to the Confluent extension tab in the sidebar.
  - Connect to the cluster you are producing message to. 
    - For Confluent Cloud, sign in via OAuth. Choose this if you have just signed up for a Confluent Cloud account.
    - If you are connecting to a cluster outside of Confluent Cloud, or if you only have access to a specific cluster in Confluent Cloud via API keys, use Direct Connection.
  - Select the cluster you're connecting to.
  - Locate the topic you're producing to while configuring the project, and click on the icon to view messages.
  - Confirm the 10 sample messages are produced to the topic.

> [!TIP]
> Can’t get the project working? You can find pre-generated projects in the `1-project-setup` folder. Go to the folder for your preferred language, and continue with step 2 of the workshop.


### 2. Customizing the Producer
Let’s make the producer emit messages from real sample data.

- Locate the producer code file (e.g., `producer.py`) from your project folder.
- Download and copy `sample_data.json` into project's root folder.
- Toggle on GitHub Copilot chat window.
- Make sure you are in **Edit** mode.
- Copilot should recommend the currently opened file, e.g. `producer.py` as context, select to accept it.
- Select "Add Context...", and choose the `sample_data.json` file in the same folder to include it as additional context.
- Use Copilot to rewrite the logic so it reads from the JSON file and produces records that match the sample data format.
    - Prompt Copilot to update the code and use content of `sample_data.json` to generate messages.
      > [!NOTE]
      > Suggested prompt: Update `producer.py`, instead of generating hardcoded messages, read the content in `sample_data.json`, generate and send messages based on its content.
    - Review Copilot's suggestions and accept or refine as needed.
- Save your changes to `producer.py`.
- Run the producer code again and confirm that it now reads from the CSV and produces the correct records.
  ```shell
  ./producer.py
  ```
- In the Confluent for VSCode extension sidebar, find your Kafka cluster and topic.
- Right-click the topic and select "View Messages".
- Confirm that the produced messages match the sample data.

> [!TIP]
> If you have trouble updating the project code using copilot, you can find pre-generated projects in the `2-project-modify` folder. Go to the folder for your preferred language and use it to proceed with the workshop.

### 3. Querying Data with Flink

- Open a new tab, and set the language mode to `Flink SQL`.
- We will start with a simple query to first make sure it works.
  ```sql
  SELECT * FROM <your_topic>;
  ```
- Submit the query.
- Use the query result viewer to confirm data is returned as expected.

### 4. Aggregating Sales Orders

- Edit your Flink SQL script to aggregate sales orders in a time window. For example:
  ```sql
  SELECT
    TUMBLE_START(event_time, INTERVAL '5' MINUTE) AS window_start,
    COUNT(*) AS order_count,
    COLLECT_LIST(item) AS items
  FROM <your_topic>
  GROUP BY TUMBLE(event_time, INTERVAL '5' MINUTE);
  ```
- Submit the query.
- Review the results in the query result viewer.

### 5. Enhancing the Query

- A new requirement: add a column for the total order amount per window.
- Use GitHub Copilot to help modify the query, e.g.:
  ```sql
  SELECT
    TUMBLE_START(event_time, INTERVAL '5' MINUTE) AS window_start,
    COUNT(*) AS order_count,
    COLLECT_LIST(item) AS items,
    SUM(order_amount) AS total_amount
  FROM <your_topic>
  GROUP BY TUMBLE(event_time, INTERVAL '5' MINUTE);
  ```
- Review Copilot's suggestion, accept if correct, and resubmit the query.
- Confirm the new column appears and values are as expected.

---

## Key Takeaways

- Simulate real-world data pipelines without production access.
- Use Confluent for VSCode extension for local, inner-loop development.
- Leverage GitHub Copilot to accelerate code and query authoring.
- Validate data flow and transformations end-to-end before production deployment.

---

Let's get started!
