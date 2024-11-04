import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://cybersafeguard-facer-default-rtdb.firebaseio.com/"
})

ref = db.reference('Residents')

data = {
    "609757":
        {
            "name": "Ismael Mendez",
            "rut": "20389177-6",
            "house_number": "415",
            "starting_year": 2018,
            "total_income": 1,
            "last_entry_time": "2023-09-20 00:54:35"
        },

    "963852":
        {
            "name": "Elon Musk",
            "rut": "14067885-k",
            "house_number": "1315",
            "starting_year": 2014,
            "total_income": 18,
            "last_entry_time": "2023-07-13 05:12:05"
        },

    "123456":
        {
            "name": "Profe Felipe",
            "rut": "12345678-k",
            "house_number": "114",
            "starting_year": 2023,
            "total_income": 0,
            "last_entry_time": "2023-10-04 16:56:52"
        }
}

for key, value in data.items():
    ref.child(key).set(value)
