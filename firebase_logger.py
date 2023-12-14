import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime

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
                    'latest_session':player.joined_at,
                    'sessions_dmed':0,
                    'latest_session_dmed':player.joined_at
                })
                count += 1
        return count

    def log_session(self, collection, players, gm):
        self.log_players(collection,players)
        doc_ref = collection.document(str(gm.id))
        sessions_played = doc_ref.get().to_dict()['sessions_played']
        sessions_dmed = doc_ref.get().to_dict()['sessions_dmed']
        doc_ref.update({
            'sessions_played': sessions_played+1,
            'latest_session': datetime.now(),
            'sessions_dmed': sessions_dmed+1,
            'latest_session_dmed': datetime.now()
        })
        for player in players:
            doc_ref = collection.document(str(player.id))
            sessions = doc_ref.get().to_dict()['sessions_played']
            doc_ref.update({
                'sessions_played': sessions+1,
                'latest_session': datetime.now()
            })
    
    def get_inactive_players(self, collection, players: list):
        inactive_players = []
        cur_date = datetime.now()
        for player in players:
            doc_ref = collection.document(str(player.id))
            activity = cur_date - doc_ref.to_dict()['latest_session']
            if activity.days > 60:
                inactive_players.append(player)
        return inactive_players
    
    def get_inactive_gms(self, collection, gms: list):
        inactive_gms = []
        cur_date = datetime.now()
        for gm in gms:
            doc_ref = collection.document(str(gm.id))
            activity = cur_date - doc_ref.to_dict()['latest_session_dmed']
            if activity.days > 60:
                inactive_gms.append(gm)
        return inactive_gms
    
    def set_preference(self, json_data, collection_name):
        collection_ref = self.db.collection(collection_name)
        for key, value in json_data.items():
            document_ref = collection_ref.document(key)
            document_ref.set(value)

    def get_preference(self, collection_name):
        collection_ref = self.db.collection(collection_name)
        data = {}
        for doc in collection_ref.stream():
            data[doc.id] = doc.to_dict()
        return data
