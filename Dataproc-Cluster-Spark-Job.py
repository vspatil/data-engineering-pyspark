import pyspark
import argparse 
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

parser = argparse.ArgumentParser()

parser.add_argument('--input_green',required='False')
parser.add_argument('--input_yellow',required='False')
parser.add_argument('--output',required='False')

args = parser.parse_args()

input_green = args.input_green
input_yellow = args.input_yellow
output = args.output


spark = SparkSession.builder.appName('test').getOrCreate()


df_green = spark.read.parquet(input_green)
df_green = df_green.withColumnRenamed('lpep_pickup_datetime','pickup_datetime').withColumnRenamed('lpep_dropoff_datetime','dropoff_datetime')

df_yellow = spark.read.parquet(input_yellow)
df_yellow = df_yellow.withColumnRenamed('tpep_pickup_datetime','pickup_datetime').withColumnRenamed('tpep_dropoff_datetime','dropoff_datetime')

common_columns = [
    'VendorID',
    'pickup_datetime',
    'dropoff_datetime',
    'store_and_fwd_flag',
    'RatecodeID',
    'PULocationID',
    'DOLocationID',
    'passenger_count',
    'trip_distance',
    'fare_amount',
    'extra',
    'mta_tax',
    'tip_amount',
    'tolls_amount',
    'improvement_surcharge',
    'total_amount',
    'payment_type',
    'congestion_surcharge'
    ]


df_green_sel=df_green.select(common_columns).withColumn('service_type',F.lit('green'))
df_yellow_sel=df_yellow.select(common_columns).withColumn('service_type',F.lit('yellow'))

df_trips_data = df_green_sel.unionAll(df_yellow_sel)
df_trips_data.createOrReplaceTempView('trips_data')

df_result = spark.sql("""
    SELECT 
    -- Reveneue grouping 
    PULocationID AS revenue_zone,
    date_trunc('month', pickup_datetime) AS revenue_month, 
    service_type, 

    -- Revenue calculation 
    SUM(fare_amount) AS revenue_monthly_fare,
    SUM(extra) AS revenue_monthly_extra,
    SUM(mta_tax) AS revenue_monthly_mta_tax,
    SUM(tip_amount) AS revenue_monthly_tip_amount,
    SUM(tolls_amount) AS revenue_monthly_tolls_amount,
    SUM(improvement_surcharge) AS revenue_monthly_improvement_surcharge,
    SUM(total_amount) AS revenue_monthly_total_amount,
    SUM(congestion_surcharge) AS revenue_monthly_congestion_surcharge,

    -- Additional calculations
    AVG(passenger_count) AS avg_montly_passenger_count,
    AVG(trip_distance) AS avg_montly_trip_distance
    FROM
    trips_data
    GROUP BY
    1, 2, 3
    """)

df_result.coalesce(1).write.parquet(output, mode='overwrite')



#run the below script to submit this job to spark cluster

#URL= "spark://de-instance.us-west1-c.c.peerless-return-376206.internal:7077"
#spark-submit --master = "spark://de-instance.us-west1-c.c.peerless-return-376206.internal:7077"\
#    python Spark_dataproc_cluster.py --input_green=data/raw/green/2021/* --input_yellow=data/raw/yellow/2021/* --output=data/report/revenue/

# --input_green=gs://de_taxi_data/raw/green/2021/* --input_yellow=gs://de_taxi_data/raw/yellow/2021/* --output=gs://de_taxi_data/report/revenue/2021



