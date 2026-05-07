import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "陳芯霈",
  "mail": "lucyamy23780983@gmail.com",
  "lab": 861
}

doc_ref = db.collection("靜宜資管2026").document("xinpei")
doc_ref.set(doc)
