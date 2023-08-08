# text-to-flinksql-demo

Demo repo for running Flink and Kafka locally using Docker and an application to generate FlinkSQL from text using ChatGPT

**Prerequisites:**

Install Docker and Docker compose locally
Before running make sure to replace your Azure key in docker-compose.yaml

**WARNING: Do not checkin the Azure key when doing a commit**

**Steps**

Build:

1. Build the app

```
docker-compose up --build -d
```

This builds and brings up all the containers in the backgroud

2. Start a FlinkSQL client

```
docker compose run sql-client
```

3. Now lets create a destination table which maps to a Kafka topic

```
CREATE TABLE pageviews_kafka (
  `url` STRING,
  `user_id` STRING,
  `browser` STRING,
  `ts` TIMESTAMP(3)
) WITH (
  'connector' = 'kafka',
  'topic' = 'pageviews',
  'properties.group.id' = 'demoGroup',
  'scan.startup.mode' = 'earliest-offset',
  'properties.bootstrap.servers' = 'kafka:9092',
  'value.format' = 'json',
  'sink.partitioner' = 'fixed'
);
```

4. Now create the source table in Flink which keeps generating mock data into the table using the mocker in Flink

```
CREATE TABLE `pageviews` (
  `url` STRING,
  `user_id` STRING,
  `browser` STRING,
  `ts` TIMESTAMP(3)
)
WITH (
  'connector' = 'faker',
  'rows-per-second' = '10',
  'fields.url.expression' = '/#{GreekPhilosopher.name}.html',
  'fields.user_id.expression' = '#{numerify ''user_##''}',
  'fields.browser.expression' = '#{Options.option ''chrome'', ''firefox'', ''safari'')}',
  'fields.ts.expression' =  '#{date.past ''5'',''1'',''SECONDS''}'
);
```

You can view the data being created using:

```
SELECT * FROM pageviews;
```

5. Now lets publish data to Kafka using the destination sink

```
INSERT INTO pageviews_kafka SELECT * FROM pageviews;
```

6. Now you can read and test queries over the data in Kafka

```
SELECT * FROM pageviews_kafka;

SELECT browser, COUNT(*) FROM pageviews_kafka GROUP BY browser;
```

7. Remember to tear down the setup when done.

- type `quit;` into flink client to exit
- Run to teardown all the containers:

```
docker-compose down
```

**Resources**

Flink setup and queries using https://github.com/confluentinc/learn-apache-flink-101-exercises/tree/master
