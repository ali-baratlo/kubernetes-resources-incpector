import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from .logger import logger

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017/").strip().strip('"').strip("'")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "odin")

client = None
db = None

def get_db():
    """
    Returns a reference to the MongoDB database instance, creating the connection if it doesn't exist.
    """
    global client, db
    if db is None:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # The ismaster command is cheap and does not require auth.
            client.admin.command('ismaster')
            logger.info("Successfully connected to MongoDB.")
            db = client[MONGO_DB_NAME]
        except ConnectionFailure as e:
            logger.critical(f"Failed to connect to MongoDB: {e}", exc_info=True)
            # This exception will be caught during startup
            raise
    return db

def get_resource_collection():
    """
    Returns a reference to the 'resources' collection in the database.
    """
    database = get_db()
    return database.resources

def get_audit_log_collection():
    """
    Returns a reference to the 'audit_logs' collection in the database.
    """
    database = get_db()
    return database.audit_logs
