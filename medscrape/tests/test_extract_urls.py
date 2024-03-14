
import os
import lancedb

# Connect to the LanceDB database and print URLs stored in the ExtractedData table
uri = os.getenv("LANCE_DB_URI")
db = lancedb.connect(uri)
tbl = db.open_table("ExtractedData")

print(db.table_names())

print(tbl.search().to_arrow())


# # Print the retrieved URLs
# for url in urls:
#     print(url)