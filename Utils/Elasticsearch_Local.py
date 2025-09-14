from elasticsearch import Elasticsearch, exceptions
import logging
import uuid


country_to_code = {
    "mappings": {
        "properties": {
            "country": {"type": "keyword"},
            "code": {"type": "integer"},
            "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
        }
    },
    "settings": {
        "index.lifecycle.name": None,
        "number_of_shards": 3,
        "number_of_replicas": 1
    }
}

zomato_restaurants = {
    "mappings": {
        "properties": {
            "restaurant_id": {"type": "keyword"},
            "restaurant_name": {"type": "keyword"},
            "country_code": {"type": "keyword"},
            "city": {"type": "keyword"},
            "address": {"type": "text"},
            "locality": {"type": "text"},
            "locality_verbose": {"type": "text"},
            "location": {
                "type": "geo_point"
            },
            "cuisines": {"type": "text"},
            "average_cost_for_two": {"type": "text"},
            "currency": {"type": "keyword"},
            "has_table_booking": {"type": "text"},
            "has_online_delivery": {"type": "text"},
            "is_delivering_now": {"type": "text"},
            "price_range": {"type": "float"},
            "aggregate_rating": {"type": "float"},
            "rating_color": {"type": "keyword"},
            "rating_text": {"type": "text"},
            "votes": {"type": "integer"},
            "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
        }
    },
    "settings": {
        "index.lifecycle.name": None,
        "number_of_shards": 3,
        "number_of_replicas": 1
    }
}

michelin_restaurants = {
    "mappings": {
        "properties": {
            "name": {"type": "keyword"},
            "year": {"type": "keyword"},
            "location": {
                "type": "geo_point"
            },
            "star": {"type": "keyword"},
            "city": {"type": "keyword"},
            "region": {"type": "keyword"},
            "zipCode": {"type": "keyword"},
            "cuisine": {"type": "text"},
            "price": {"type": "keyword"},
            "url": {"type": "text"},
            "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"}
        }
    },
    "settings": {
        "index.lifecycle.name": None,
        "number_of_shards": 3,
        "number_of_replicas": 1
    }
}

index_mapping = {
    "country_to_code_zomato": country_to_code,
    "zomato_restaurants": zomato_restaurants,
    "michelin_restaurants": michelin_restaurants
}

class ElasticCache:
    def __init__(self, index_name):
        self.index_name = index_name
        self.client = Elasticsearch("http://localhost:9200")
        self._create_index()

    def _create_index(self):
        try:
            if not self.client.indices.exists(index=self.index_name):
                self.client.indices.create(
                    index=self.index_name,
                    body=index_mapping[self.index_name]
                )
                logging.info(f"Index '{self.index_name}' created successfully.")
        except exceptions as e:
            logging.error(f"Error creating index: {e}")

    def save_to_cache(self, document: dict):
        try:
            doc_id = str(list(document.values())[0]) + str(uuid.uuid4())
            self.client.index(index=self.index_name, id=doc_id, body=document)
            logging.info(f"Document saved to cache with ID: {doc_id}")
        except exceptions as e:
            logging.error(f"Error saving document to cache: {e}")

    def search_cache(self, query: dict):
        return_data = []
        try:
            result = self.client.search(index=self.index_name, body={"query": query})
            if result["hits"]["total"]["value"] > 0:
                for hit in result["hits"]["hits"]:
                    return_data.append(hit["_source"])
                return return_data
            return return_data 
        except Exception as e:
            logging.error(f"Error searching cache: {e}")
            return None

    def delete_from_cache(self, query: dict):
        try:
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