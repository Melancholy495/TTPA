from datetime import datetime
from elasticsearch import Elasticsearch, exceptions
import logging

class ElasticCache:
    def __init__(self, index_name="api_cache"):
        self.index_name = index_name
        self.client = Elasticsearch("http://localhost:9200")
        self._create_index()

    def _create_index(self):
        try:
            if not self.client.indices.exists(index=self.index_name):
                self.client.indices.create(
                    index=self.index_name,
                    body={
                        "mappings": {
                            "properties": {
                                "category": {"type": "keyword"},
                                "tool_name": {"type": "keyword"},
                                "api_name": {"type": "keyword"},
                                "api_args": {"type": "keyword"},
                                "response": {"type": "text"},
                                "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
                            }
                        },
                        "settings": {
                            "index.lifecycle.name": None,
                            "number_of_shards": 3,
                            "number_of_replicas": 1
                        }
                    }
                )
                logging.info(f"Index '{self.index_name}' created successfully.")
        except exceptions as e:
            logging.error(f"Error creating index: {e}")

    def save_to_cache(self, payload, response):
        try:
            document = {
                "category": payload["category"],
                "tool_name": payload["tool_name"],
                "api_name": payload["api_name"],
                "api_args": payload["api_args"],
                "response": response,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            doc_id = f"{payload['category']}_{payload['tool_name']}_{payload['api_name']}_{hash(str(payload['api_args']))}"
            self.client.index(index=self.index_name, id=doc_id, body=document)
            logging.info(f"Document saved to cache with ID: {doc_id}")
        except exceptions as e:
            logging.error(f"Error saving document to cache: {e}")

    def search_cache(self, payload):
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"category": payload["category"]}},
                        {"term": {"tool_name": payload["tool_name"]}},
                        {"term": {"api_name": payload["api_name"]}},
                        {"term": {"api_args": payload["api_args"]}}
                    ]
                }
            }

            result = self.client.search(index=self.index_name, body={"query": query})
            if result["hits"]["total"]["value"] > 0:
                return result["hits"]["hits"][0]["_source"]
            return None 
        except Exception as e:
            logging.error(f"Error searching cache: {e}")
            return None

    def delete_from_cache(self, payload):
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"category": payload["category"]}},
                        {"term": {"tool_name": payload["tool_name"]}},
                        {"term": {"api_name": payload["api_name"]}},
                        {"term": {"api_args": payload["api_args"]}}
                    ]
                }
            }

            result = self.client.search(index=self.index_name, body={"query": query})
            if result["hits"]["total"]["value"] > 0:
                doc_id = result["hits"]["hits"][0]["_id"]

                self.client.delete(index=self.index_name, id=doc_id)
                logging.info(f"Document with ID {doc_id} deleted from cache.")
                return True
            else:
                logging.info("No matching document found to delete.")
                return False
        except Exception as e:
            logging.error(f"Error deleting document from cache: {e}")
            return False

    def clear_cache(self):
        try:
            self.client.indices.delete(index=self.index_name, ignore=[400, 404])
            self._create_index()
            logging.info(f"Cache cleared and index '{self.index_name}' recreated.")
        except exceptions as e:
            logging.error(f"Error clearing cache: {e}")
