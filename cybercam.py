import os
import pickle
import cv2
import numpy as np
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from pygame import mixer
from time import strftime
import time
from datetime import datetime
import threading

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://cybersafeguard-facer-default-rtdb.firebaseio.com/",
    'storageBucket': "cybersafeguard-facer.appspot.com"
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')

# Import img en la lista

folderModePath = 'Resources/Modes'
modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

# Cargar el encoding file
file = open('EncodeFile.p', 'rb')
encodeListIds = pickle.load(file)
file.close()
encodeListK, personasId = encodeListIds
# print(personasId)
print("Archivo Cargado")

modeType = 0
counter = 0
id = -1
imgPerson = []

# Variable para indicar si se está esperando
esperando = False

# Crear la carpeta para las fotos si no existe
carpeta_fotos = "Rostros No Identificados"
if not os.path.exists(carpeta_fotos):
    os.makedirs(carpeta_fotos)


def obtener_hora_actual():
    return strftime('%H:%M:%S %p')


def tomar_foto():
    # Capturar un solo cuadro
    ret, frame = cap.read()
    if ret:

        fecha_hora_actual = datetime.now()
        formato_fecha_hora = fecha_hora_actual.strftime("%d-%m-%Y_%H_%M_%S")

        # Nombre del archivo de salida
        nombre_archivo = os.path.join(carpeta_fotos, "Desconocido"+f"_{formato_fecha_hora}.jpg")

        cv2.imwrite(nombre_archivo, frame)
        print(f"Foto tomada y guardada como {nombre_archivo}")

# Función para tomar una foto después de 5 segundos
def foto_despues_5_segundos():
    global esperando
    esperando = True
    print("Esperando 5 segundos...")
    time.sleep(5)
    tomar_foto()
    esperando = False

while True:
    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceFrame = face_recognition.face_locations(imgS)
    encodeFrame = face_recognition.face_encodings(imgS, faceFrame)

    # Agrega la hora actual al fotograma
    hora_actual = obtener_hora_actual()

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    cv2.putText(imgBackground, hora_actual, (68, 630)
                , cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)


    if faceFrame:
        for encodeFace, faceLoc in zip(encodeFrame, faceFrame):
            matches = face_recognition.compare_faces(encodeListK, encodeFace)
            faceDis = face_recognition.face_distance(encodeListK, encodeFace)
            print("Matches: ", matches)
            print("FaceDIS: ", faceDis)

            matchIndex = np.argmin(faceDis)
            #print("Posición Identificada", matchIndex)

            if matches[matchIndex]:  #Si el rostro en camara coincide con algun rostro registrado

                # Cuadro verde de reconocimiento
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = personasId[matchIndex]

                #Mensaje en pantalla
                cvzone.putTextRect(imgBackground, "Identificando..", (260,575), colorR=(0, 255, 0))

                if counter == 0:

                    cv2.imshow("Cyber Safe Guard - Reconocimiento Facial", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

            else: #Si el rostro en camara NO coincide con algun rostro registrado

                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0, colorC=(0, 0, 255))
                cvzone.putTextRect(imgBackground, "No identificado", (130, 575), colorR=(0, 0, 255))

                #Reproduce audio de Alarma
                mixer.init()
                if not esperando:
                    threading.Thread(target = foto_despues_5_segundos).start()
                    mixer.music.load('Sounds/alarma.ogg')
                    mixer.music.play()

        if counter != 0:

            if counter == 1:
                # Obtener la data
                personasInfo = db.reference(f'Residents/{id}').get()
                print(personasInfo)
                # Obtener la imagen desde Storage
                blob = bucket.get_blob(f'Images/{id}.png')
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                imgPerson = cv2.imdecode(array, cv2.COLOR_BGRA2RGB)
                # Update data de ingresos
                datetimeObject = datetime.strptime(personasInfo['last_entry_time'],
                                                   "%Y-%m-%d %H:%M:%S")
                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                print(secondsElapsed)

                #Reproduce audio de reconocimiento
                mixer.init()
                mixer.music.load('Sounds/identificacion.ogg')
                mixer.music.play()

                if secondsElapsed > 7:
                    ref = db.reference(f'Residents/{id}')
                    personasInfo['total_income'] += 1
                    ref.child('total_income').set(personasInfo['total_income'])
                    ref.child('last_entry_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    modeType = 3
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            if modeType != 3:

                if 15 < counter < 20:
                    modeType = 2

                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if counter <= 15:
                    cv2.putText(imgBackground, str(personasInfo['total_income']), (860, 134),
                                  cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    cv2.putText(imgBackground, str(personasInfo['house_number']), (1015, 553),
                                 cv2.FONT_HERSHEY_COMPLEX, 0.7, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(id), (915, 626),
                                 cv2.FONT_HERSHEY_COMPLEX, 0.7, (100, 100, 100), 2)
                    cv2.putText(imgBackground, str(personasInfo['rut']), (1006, 495),
                                 cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 255, 255), 1)
                    cv2.putText(imgBackground, str(personasInfo['starting_year']), (1115, 626),
                                 cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 2)

                    (w, h), _ = cv2.getTextSize(personasInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w) // 2
                    cv2.putText(imgBackground, str(personasInfo['name']), (808 + offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                    imgBackground[184:184 + 216, 907:907 + 216] = imgPerson

                counter += 1

                if counter >=20:
                    counter = 0
                    modeType = 0
                    personasInfo = []
                    imgPerson = []
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]
    else:
        modeType = 0
        counter = 0

       # cvzone.putTextRect(imgBackground, "No identificado", (150, 400), colorR= (0, 0, 255))

    cv2.imshow("Cyber Safe Guard - Reconocimiento Facial", imgBackground)
    if cv2.waitKey(1) & 0xFF == 27:  # Sale del bucle cuando se presiona la tecla Esc
        break

cap.release()
cv2.destroyAllWindows()

