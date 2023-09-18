import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def sending_data_mongodb(df):

    mdb_uname = os.getenv("MDB_UNAME")
    mdb_passwd = os.getenv("MDB_PASSWD")
    mdb_hostname = os.getenv("MDB_HOSTNAME")
    mdb_table = os.getenv("MDB_TABLE")
    mdb_collect_name = os.getenv("MDB_COLLECT_NAME")

    mongo_conn = f"mongodb+srv://{mdb_uname}:{mdb_passwd}@{mdb_hostname}/{mdb_table}"
    client = MongoClient(mongo_conn)
    db = client[os.getenv('MDB_TABLE')]
    records = df.to_dict(orient='records')
    collection = db[os.getenv('MDB_COLLECT_NAME')]

    try:
        collection.insert_many(records)
        print("SUCCESSFULL INSERTED RECORDS VIA MONGODB!!!\n")
    except Exception as e:
        print(e)