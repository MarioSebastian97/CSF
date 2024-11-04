import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://cybersafeguard-facer-default-rtdb.firebaseio.com/",
    'storageBucket': "cybersafeguard-facer.appspot.com"
})

# Importar imagenes de las personas

folderPath = 'Images'
pathList = os.listdir(folderPath)
print(pathList)
imageList = []
idPersonas = []
for path in pathList:
    imageList.append(cv2.imread(os.path.join(folderPath, path)))
    idPersonas.append(os.path.splitext(path)[0])

    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)

    # print(os.path.splitext(path)[0])
print(idPersonas)


def find_encoding(image_list):
    encode_list = []
    for img in image_list:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encode_list.append(encode)
    return encode_list


print("Encoding Started...")
encodeListK = find_encoding(imageList)
encodeListId = [encodeListK, idPersonas]
print(encodeListK)
print("Encoding Complete")

file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListId, file)
file.close()
print("File Saved")
