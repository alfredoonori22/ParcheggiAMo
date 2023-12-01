import datetime
import fnmatch
import time
from flask import Flask
from flask import request
from flask import Response
import requests
import paho.mqtt.client as mqtt
import threading

TOKEN = "5644441139:AAHhAOqHw_RRqvYZKKl-zsHt6q2XEekqgEM"
# https://api.telegram.org/bot5644441139:AAHhAOqHw_RRqvYZKKl-zsHt6q2XEekqgEM/setWebhook?url=https://a3fd-151-68-53-131.eu.ngrok.io
# ngrok http 5000
broker = 'broker.emqx.io'
broker_port = 1883

app = Flask(__name__)

global chat_id
global park_num   # numero parcheggio (1,2,3)
global pieno
txt = ''
state = 0
post_num = 100   # numero postazione (1,2,3)
tariffe = [1, 1, 1]   #vettore tariffe
prenotazioni = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]   # ID ricevuti con e senza prenotazione
start_times = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]    # istante in cui inizia il timer
parks = {1: "Viali",
         2: "Teatro Storchi",
         3: "Stadio"}

'''
stato 0 = non ho ancora prenotato/occupato nulla
stato 1 = scelgo il parcheggio
stato 2 = selezione ID/prenotazione
stato 3 = Hai già un ID?
stato 4 = inserimento ID, ho ricevuto l'id ed è corretto, devo comunicare con raspberry per ottenere la postazione
stato 5 = prenotazione posto
stato 6 = devo inserire l'ID della prenotazione
stato 7 = verifico le informazioni per lo stato del parcheggio
'''


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    mqtt_client.subscribe(topic_id)
    mqtt_client.subscribe(topic_risposta)
    mqtt_client.subscribe(topic_prenotazioni)
    mqtt_client.subscribe(topic_timer)
    mqtt_client.subscribe(topic_tariffe)
    mqtt_client.subscribe(topic_pieno)


def on_message(client, userdata, message):
    global park_num, post_num, prenotazioni, start_times, pieno, parks

    msg = message.payload.decode()
    print('Ho ricevuto il messaggio: ' + msg + ' dal topic ' + message.topic)

    if mqtt.topic_matches_sub(topic_id, message.topic):
        park_num = int(message.topic.split('/')[1][-1])
        post_num = int(message.topic.split('/')[2][-1])
        prenotazioni[int(park_num) - 1][int(post_num) - 1] = msg
        print(prenotazioni)

    elif mqtt.topic_matches_sub(topic_risposta, message.topic):
        post_num = msg

    elif mqtt.topic_matches_sub(topic_prenotazioni, message.topic):
        park_num = int(message.topic.split('/')[1][-1])
        post_num = int(message.topic.split('/')[2][-1])
        prenotazioni[int(park_num) - 1][int(post_num) - 1] = msg

    elif mqtt.topic_matches_sub(topic_timer, message.topic):
        park_num = int(message.topic.split('/')[1][-1])
        post_num = int(message.topic.split('/')[2][-1])
        if msg == "0":
            tel_send_message("Errore: Timer inconsistente")
            state = 0
        else:
            end_time = (datetime.datetime.now().timestamp() - float(msg)) // 1
            tel_send_message(f"Hai liberato il posto {post_num} del parcheggio {parks[int(park_num)]} dopo {end_time} secondi\n"
                             f"Il totale da pagare è: €{(end_time * float(tariffe[int(park_num)-1]))/100}\n"
                             f"Grazie e arrivederci!")
            mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/state', 0)
            prenotazioni[int(park_num)-1][int(park_num)-1] = 0
            state = 0

    elif mqtt.topic_matches_sub(topic_tariffe, message.topic):
        park_num = int(message.topic.split('/')[1][-1])
        tariffe[int(park_num)-1] = msg

    elif mqtt.topic_matches_sub(topic_pieno, message.topic):
        pieno = msg


def tel_parse_message(message):
    global chat_id, txt

    print("message-->", message)
    try:
        chat_id = message['message']['chat']['id']
        txt = message['message']['text']
        print("chat_id-->", chat_id)
        print("txt-->", txt)

        return chat_id, txt
    except:
        print("NO text found-->>")


def tel_parse_button(message):
    try:
        bottone = message['callback_query']['data']
        print("button_pressed-->", bottone)
        return bottone
    except:
        print("NO button found-->>")


def tel_send_message(text):
    global chat_id
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }

    r = requests.post(url, json=payload)

    return r


def tel_send_inlinebutton():
    global chat_id

    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': "Che operazione vuoi eseguire?",
        'reply_markup': {
            "inline_keyboard": [[
                {
                    "text": "ID Display",
                    "callback_data": "inserimento"
                },
                {
                    "text": "Prenotazione",
                    "callback_data": "prenotazione"
                },
                {
                    "text": "Stato sosta",
                    "callback_data": "stato"
                }]
            ]
        }
    }

    r = requests.post(url, json=payload)

    return r


def tel_send_singlebutton():
    global chat_id, post_num

    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': f"Quale operazione vuoi eseguire?",
        'reply_markup': {
            "inline_keyboard": [[
                {
                    "text": "Cancella prenotazione",
                    "callback_data": 'canc'
                },
                {
                    "text": "Torna indietro",
                    "callback_data": "back"
                }]
            ]
        }
    }

    r = requests.post(url, json=payload)

    return r


def tel_send_resbutton():
    global chat_id, post_num

    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': f"La postazione numero {post_num} è libera. Vuoi prenotarla?",
        'reply_markup': {
            "inline_keyboard": [[
                {
                    "text": "Si",
                    "callback_data": 'yes'
                },
                {
                    "text": "No",
                    "callback_data": "no"
                }]
            ]
        }
    }

    r = requests.post(url, json=payload)

    return r


def tel_send_inlineparcheggi():
    global chat_id

    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'

    payload = {
        'chat_id': chat_id,
        'text': "Seleziona un parcheggio",
        'reply_markup': {
            "inline_keyboard": [[
                {
                    "text": "Viali",
                    "callback_data": "1"
                },
                {
                    "text": "Teatro Storchi",
                    "callback_data": "2"
                },
                {
                    "text": "Stadio",
                    "callback_data": "3"
                }]
            ]
        }
    }

    r = requests.post(url, json=payload)

    return r


@app.route('/', methods=['GET', 'POST'])
def index():
    global state, chat_id, prenotazioni, park_num, post_num, txt, start_times, pieno, parks

    if request.method == 'POST':
            msg = request.get_json()

        #try:
            if state == 0:
                chat_id, txt = tel_parse_message(msg)
                tel_send_message("Benvenuto!")
                tel_send_inlineparcheggi()

                # stampo su lcd i posti disponibili
                mqtt_client.publish(f"parcheggio/parcheggio_1/lcd", 1)
                state = 1

            elif state == 1:
                park_num = tel_parse_button(msg)
                mqtt_client.publish('parcheggio/park_id', park_num)
                tel_send_inlinebutton()
                state = 2

            elif state == 2:
                bottone = tel_parse_button(msg)

                if bottone == 'inserimento':
                    # gestione senza prenotazione
                    mqtt_client.publish(f"parcheggio/parcheggio_{park_num}/richiesta", 0)
                    time.sleep(0.5)                # richiedo un posto nel parcheggio park_num
                    # se è -1 vuol dire che non ci sono posto liberi, passo allo stato 4, altrimenti continuo con lo stato 2
                    if pieno == '1':
                        tel_send_message("Questo parcheggio non ha posti disponibili, arrivederci!")
                        state = 0
                    else:
                        mqtt_client.publish(f"parcheggio/parcheggio_{park_num}/richiesta", 1)
                        time.sleep(0.5)
                        mqtt_client.publish(f"parcheggio/parcheggio_{park_num}/postazione_{post_num}/id", -1)
                        time.sleep(0.5)
                        tel_send_message("Inserire l'ID mostrato nel display!")
                        state = 3

                elif bottone == 'prenotazione':
                    # gestione con prenotazione
                    # richiedo un posto nel parcheggio park_num
                    # se è -1 vuol dire che non ci sono posto liberi, passo allo stato 4, altrimenti continuo con lo stato 2
                    mqtt_client.publish(f"parcheggio/parcheggio_{park_num}/richiesta", 0)
                    time.sleep(0.5)
                    if pieno == '1':
                        tel_send_message("Questo parcheggio non ha posti disponibili, arrivederci!")
                        state = 0
                    else:
                        mqtt_client.publish(f"parcheggio/parcheggio_{park_num}/richiesta", 1)
                        time.sleep(0.5)
                        tel_send_resbutton()
                        state = 4

                elif bottone == 'stato':
                    # Voglio conoscere lo stato del mio parcheggio
                    tel_send_message("Inserisci il numero della postazione e l'ID separati da uno '/'")
                    state = 6

            elif state == 3:
                _, txt = tel_parse_message(msg)

                # Qui dobbiamo controllare che l'ID sia corretto
                # Se combacia con quello ricevuto con MQTT dalla sbarra
                if prenotazioni[int(park_num)-1][int(post_num)-1] == txt:
                    # se è uguale, mando al raspberry un bit di conferma così che possa mostrare un messaggio sul display
                    tel_send_message("L'ID è corretto!")
                    mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/state', 3)
                    # si apre la sbarra, invio un messaggio sul topic tempo
                    start_times[int(park_num)-1][int(post_num)-1] = datetime.datetime.now()
                    mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/start_time', str(start_times[int(park_num)-1][int(post_num)-1].timestamp()))
                    if not(park_num == 1 and post_num == 1):
                        mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/state', 1)

                    # Assegnazione posto e aggiornamento stato postazioni alla sbarra
                    tel_send_message(f"La postazione assegnata è la numero {post_num}.\nL'orario di inizio della sosta è {str(start_times[int(park_num)-1][int(post_num)-1].time()).split('.')[0]}")
                    state = 0
                else:
                    if txt == '/start':
                        tel_send_message("Benvenuto!")
                        tel_send_inlineparcheggi()
                        state = 1
                    else:
                        # Se non combacia manda un messaggio di errore
                        tel_send_message("L'ID è errato, riprova!")

            elif state == 4:
                # prenotazione posto
                bottone = tel_parse_button(msg)

                if bottone == 'yes':

                    tel_send_message(f"Prenotazione effettuata: parcheggio {parks[int(park_num)]}, postazione {post_num}")
                    mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/state', 2)
                    time.sleep(0.5)
                    tel_send_message(f"Il tuo ID di prenotazione è: {prenotazioni[int(park_num)-1][int(post_num)-1]}")
                    tel_send_message(f"Inseriscilo una volta giunto davanti all'ingresso del parcheggio")
                    state = 5

                elif bottone == 'no':
                    tel_send_message(f"Prenotazione non effettuata!\nGrazie e arrivederci")
                    state = 0

            elif state == 5:
                # devo inserire l'ID della prenotazione
                _, txt = tel_parse_message(msg)

                if txt in prenotazioni[int(park_num)-1]:
                    tel_send_message("L'ID è corretto!")
                    # si apre la sbarra, invio un messaggio sul topic tempo
                    start_times[int(park_num)-1][int(post_num)-1] = datetime.datetime.now()
                    mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/start_time', str(start_times[int(park_num)-1][int(post_num)-1].timestamp()))
                    if not(park_num == 1 and post_num == 1):
                        mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/state', 1)

                    tel_send_message(f"La postazione assegnata è la numero {post_num}.\nL'orario di inizio della sosta è {str(start_times[int(park_num)-1][int(post_num)-1].time()).split('.')[0]}")
                    state = 0
                elif txt == '/start':
                    tel_send_message("Benvenuto!")
                    tel_send_inlineparcheggi()
                    state = 1
                else:
                    # Se non combacia manda un messaggio di errore
                    tel_send_message("L'ID è errato, riprova!")

            elif state == 6:
                # leggo il messaggio scritto dall'utente
                _, txt = tel_parse_message(msg)

                if txt == '/start':
                    tel_send_message("Benvenuto!")
                    tel_send_inlineparcheggi()
                    state = 1
                else:
                    if fnmatch.fnmatch(txt, "[0-9]/*"):
                        post_num = txt.split('/')[0]
                        id = txt.split('/')[1]
                        if id != prenotazioni[int(park_num)-1][int(post_num)-1]:
                            tel_send_message("L'ID non corrisponde alla postazione inserita, riprova")
                        else:
                            if start_times[int(park_num)-1][int(post_num)-1] == 0:
                                tel_send_message(f"Parcheggio: {parks[int(park_num)]}\nPostazione: {post_num}\n"
                                                 f"Stato: Prenotato")
                                tel_send_singlebutton()
                                state = 7

                            else:
                                current_time = (datetime.datetime.now().timestamp() - start_times[int(park_num)-1][int(post_num)-1].timestamp()) // 1
                                tel_send_message(f"Parcheggio: {parks[int(park_num)]}\nPostazione: {post_num}\n"
                                                 f"Stato: In sosta da {current_time} secondi")
                                time.sleep(0.5)
                                tel_send_message(f"Costo attuale: €{(current_time*tariffe[int(park_num)-1])/100}")
                    else:
                        tel_send_message("Formato errato, riprova!")

            elif state == 7:
                bottone = tel_parse_button(msg)

                if bottone == 'canc':
                    print(post_num)
                    print(park_num)
                    mqtt_client.publish(f'parcheggio/parcheggio_{park_num}/postazione_{post_num}/state', 0)
                    tel_send_message(f"La tua prenotazione è stata cancellata con successo!")
                else:
                    tel_send_message("Ok, arrivederci!")

                state = 0

        # except:
            # print("from index-->")
            return Response('ok', status=200)
    else:
        return "<h1></h1>"


def simulazione():
    while 1:
        a = input('\nParcheggio:\n')
        b = input('\nPostazione:\n')
        # simulo l'uscita di una macchina dal parcheggio
        mqtt_client.publish(f'parcheggio/parcheggio_{a}/postazione_{b}/timer', str(start_times[int(a)-1][int(b)-1].timestamp()))
        print(f'Ho cambiato lo stato del parcheggio {a}, postazione {b} in 3 (terminato)')


topic_id = 'parcheggio/+/+/id'
topic_risposta = 'parcheggio/+/risposta'
topic_prenotazioni = 'parcheggio/+/+/prenotazioni'
topic_timer = 'parcheggio/+/+/timer'
topic_tariffe = 'parcheggio/+/tariffe'
topic_pieno = 'parcheggio/+/pieno'

mqtt_client = mqtt.Client('Telegram')
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to " + broker + " port: " + str(broker_port))
mqtt_client.connect(broker, broker_port)

t1 = threading.Thread()
t1.start()
t2 = threading.Thread(target=mqtt_client.loop_forever)
t2.start()
t3 = threading.Thread(target=simulazione)
t3.start()

if __name__ == '__main__':
    app.run(threaded=True)
