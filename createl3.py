import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "陳芯霈5",
  "mail": "lucyamy23780983@gmail.com",
  "lab": 123
}


collection_ref = db.collection("靜宜資管")
collection_ref.add(doc)
