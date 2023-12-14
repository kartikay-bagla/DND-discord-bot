import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import Secrets

class FirebaseClient:
    def __init__(self,creds_path):
        self.cred = credentials.Certificate(creds_path)
        self.app = firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

    def get_collection(self, collection_name: str):
        return self.db.collection(collection_name)
    
    def log_players(self, collection, players: list):
        count = 0
        for player in players:
            doc_ref = collection.document(str(player.id))
            if not doc_ref.get().exists:
                doc_ref.set({
                    'player_name':player.name,
                    'player_joined_date':player.joined_at,
                    'sessions_played':0,
                    'latest_session':None,
                    'sessions_dmed':0,
                    'latest_session_dmed':None
                })
                count += 1
        return count
        
    
# client = FirebaseClient(Secrets.FIREBASE_CRED_PATH)
# test_collection = client.get_collection()
# client.log_players(test_collection,[308948674271248385,1,2])