from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

# Initialize Spark session with Hive support
spark = SparkSession.builder \
    .appName("PopulateUsers") \
    .enableHiveSupport() \
    .config("hive.metastore.uris", "thrift://hive-metastore:9083") \
    .getOrCreate()

# Define the schema
schema = StructType([
    StructField("nom", StringType(), True),
    StructField("prenom", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("ca", DoubleType(), True)
])

# Sample data
data = [
    ("Dupont", "Jean", 35, 50000.0),
    ("Martin", "Marie", 28, 65000.0),
    ("Bernard", "Pierre", 42, 75000.0),
    ("Thomas", "Sophie", 31, 55000.0),
    ("Robert", "Paul", 45, 85000.0)
]

# Create DataFrame
df = spark.createDataFrame(data, schema)

# Save the DataFrame as a Hive table

df.write \
    .format("hive") \
    .mode("overwrite") \
    .saveAsTable("default.new_users")  # you can specify database.tablename

# Show the data
df.show()

# Stop Spark session
spark.stop()