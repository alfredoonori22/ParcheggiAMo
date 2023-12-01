import time
import pymongo as pymongo
from flask import Flask, request
from flask import render_template
import paho.mqtt.client as mqtt
import threading


client = pymongo.MongoClient("mongodb+srv://chiara:OXYwmH1Aaof6v4Bn@cluster0.nzollqg.mongodb.net/?retryWrites=true&w=majority")
db = client.database
col = db['iot']

# creo la app Flask
app = Flask(__name__)

global park_id, p_id
old = ""
postation = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
ID_web = [['-', '-', '-'], ['-', '-', '-'], ['-', '-', '-']]
tariffe = [1, 1, 1]


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    mqtt_client.subscribe(topic_state)
    mqtt_client.subscribe(topic_id)
    mqtt_client.subscribe(topic_prenotazioni)
    mqtt_client.subscribe(topic_tariffe)


def write_log(id_user, park_id, p_id, state):
    global tariffe

    with open("events.log", "a+") as f:
        f.write(f'{id_user} ha cambiato lo stato del parcheggio {park_id}, postazione {p_id} nello stato: {state}, con una tariffa di: {tariffe[int(park_id)-1]} €cent/s\n')
        col.insert_one({'user': id_user, 'park': park_id, 'slot': p_id, 'state': state, 'price': f"{tariffe[int(park_id)-1]} €cent/s"})


def on_message(client, userdata, message):
    global park_id, p_id, tariffe

    msg = message.payload.decode()
    print("Ho ricevuto: " + msg + "    da " + message.topic)

    park_id = message.topic.split('/')[1][-1]
    p_id = message.topic.split('/')[2][-1]

    if mqtt.topic_matches_sub(topic_state, message.topic):
        if msg == '3':
            postation[int(park_id)-1][int(p_id)-1] = 2
            write_log(ID_web[int(park_id)-1][int(p_id)-1], park_id, p_id, "2")
        else:
            postation[int(park_id)-1][int(p_id)-1] = msg
            write_log(ID_web[int(park_id)-1][int(p_id)-1], park_id, p_id, msg)
        if msg == '0':
            ID_web[int(park_id)-1][int(p_id)-1] = '-'

    elif mqtt.topic_matches_sub(topic_id, message.topic):
        ID_web[int(park_id)-1][int(p_id)-1] = msg

    elif mqtt.topic_matches_sub(topic_prenotazioni, message.topic):
        ID_web[int(park_id)-1][int(p_id)-1] = msg

    elif mqtt.topic_matches_sub(topic_tariffe, message.topic):
        park_num = int(message.topic.split('/')[1][-1])
        tariffe[int(park_num)-1] = msg


# definisco la prima route, home
@app.route('/')
def main():
    global ID_web
    global postation
    global tariffe
    global old

    url = str(request.url)
    if '?' in url and url != old:
        old = url
        url = url.split('?')[1]
        if url[0] == "o":
            mqtt_client.publish(f"parcheggio/parcheggio_{url[6]}/postazione_1/state", 1)
            mqtt_client.publish(f"parcheggio/parcheggio_{url[6]}/postazione_2/state", 1)
            mqtt_client.publish(f"parcheggio/parcheggio_{url[6]}/postazione_3/state", 1)
        elif url[0] == "l":
            mqtt_client.publish(f"parcheggio/parcheggio_{url[6]}/postazione_1/state", 0)
            mqtt_client.publish(f"parcheggio/parcheggio_{url[6]}/postazione_2/state", 0)
            mqtt_client.publish(f"parcheggio/parcheggio_{url[6]}/postazione_3/state", 0)
        else:
            val = url.split('=')[1]
            if val != tariffe[int(url[3])-1]:
                mqtt_client.publish(f"parcheggio/parcheggio_{url[3]}/tariffe", url.split('=')[1])
                tariffe[int(url[3])-1] = val

    index = open("index.html").read().format(postation=postation, ID_web=ID_web)

    return index


broker = 'broker.emqx.io'
broker_port = 1883
message_limit = 1000

topic_state = 'parcheggio/+/+/state'
topic_id = 'parcheggio/+/+/id'
topic_prenotazioni = 'parcheggio/+/+/prenotazioni'
topic_tariffe = 'parcheggio/+/tariffe'

mqtt_client = mqtt.Client('Web')
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to " + broker + " port: " + str(broker_port))
mqtt_client.connect(broker, broker_port)

t1 = threading.Thread()
t1.start()
t2 = threading.Thread(target=mqtt_client.loop_forever)
t2.start()

# verifica se è il programma principale
# e manda in esecuzione il web server su http://localhost:5000
# in questo caso in debug, ovvero si riavvia ad ogni cambiamento dei file
if __name__ == "__main__":
    app.run(threaded=True, port=8000)

