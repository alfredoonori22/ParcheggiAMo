import string
import random
import paho.mqtt.client as mqtt
import threading

global park_id
global p_id
postation = [[]]
timer = [[]]
ID = [[]]


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    mqtt_client.subscribe(topic_state)
    mqtt_client.subscribe(topic_richiesta)
    mqtt_client.subscribe(topic_id)
    mqtt_client.subscribe(topic_timer)
    mqtt_client.subscribe(topic_parkid)


def on_message(client, userdata, message):
    global park_id, p_id

    # parte per cancellare messaggi rimasti nei topic
    # mqtt_client.publish('parcheggio/parcheggio_1/postazione_1/state', '', retain=True)

    msg = message.payload.decode()
    print("Ho ricevuto: " + msg + "    da " + message.topic)

    if mqtt.topic_matches_sub(topic_state, message.topic):
        park_id = message.topic.split('/')[1][-1]
        p_id = message.topic.split('/')[2][-1]
        # libero
        if msg == '0':
            change_state(p_id, 0)
        # occupato
        elif msg == '1':
            change_state(p_id, 1)
        # prenotato
        elif msg == '2':
            change_state(p_id, 2)
            resID_generator()

        # termine parcheggio
        elif msg == '3':
            change_state(p_id, 3)
        else:
            print('ERRORE: stato inesistente')

    elif mqtt.topic_matches_sub(topic_richiesta, message.topic):
        park_id = message.topic.split('/')[1][-1]
        libero = False
        for i in enumerate(postation[int(park_id)-1]):
            if i[1] == 0:
                if msg == '1':
                    mqtt_client.publish(f'parcheggio/parcheggio_{park_id}/risposta', i[0] + 1)
                libero = True
                break
        if not libero:
            mqtt_client.publish(f'parcheggio/parcheggio_{park_id}/risposta', -1)

    elif mqtt.topic_matches_sub(topic_parkid, message.topic):
        park_id = msg

    elif mqtt.topic_matches_sub(topic_timer, message.topic):
        park_id = message.topic.split('/')[1][-1]
        p_id = message.topic.split('/')[2][-1]

        timer[int(park_id)-1][int(p_id)-1] = msg.split('.')[0]

    elif mqtt.topic_matches_sub(topic_id, message.topic):
        park_id = message.topic.split('/')[1][-1]
        p_id = message.topic.split('/')[2][-1]

        if msg == '-1':
            id_generator()


def publish_initial_parking_info():
    global postation
    global timer
    global ID

    postation = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    timer = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    ID = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    for i in range(1, 2):
        for j in range(1, 4):
            mqtt_client.publish(f'parcheggio/parcheggio_{i}/postazione_{j}/state', 0)
            # inizializzo a 1 (occupato) i posti del parcheggio_1
    for i in range(2, 4):
        for j in range(1, 4):
            mqtt_client.publish(f'parcheggio/parcheggio_{i}/postazione_{j}/state', 0)


# lo stato del parcheggio cambia perché viene occupato senza prenotazione
def change_state(p_id, state):
    global park_id

    postation[int(park_id)-1][int(p_id)-1] = state
    # print('Ho cambiato lo stato del parcheggio ' + str(park_id) + ' alla postazione ' + str(postazione) + ' in ' + str(state))


def resID_generator():
    global park_id

    characters = string.ascii_uppercase + string.digits
    res_id = ''.join(random.choice(characters) for i in range(1))
    # comunico l'id sul topic
    mqtt_client.publish(f'parcheggio/parcheggio_{park_id}/postazione_{p_id}/prenotazioni', res_id)
    ID[int(park_id)-1][int(p_id)-1] = res_id


def id_generator():
    global park_id

    characters = string.ascii_uppercase + string.digits
    id = ''.join(random.choice(characters) for i in range(1))
    # todo: stampo sul display lcd l'ID
    # comunico l'id sul topic
    mqtt_client.publish(f'parcheggio/parcheggio_{park_id}/postazione_{p_id}/id', id)
    ID[int(park_id)-1][int(p_id)-1] = id


broker = 'broker.emqx.io'
broker_port = 1883
message_limit = 1000

topic_state = f'parcheggio/+/+/state'
topic_id = f'parcheggio/+/+/id'
topic_timer = f'parcheggio/+/+/start_time'
topic_richiesta = f'parcheggio/+/richiesta'
topic_parkid = 'parcheggio/park_id'

mqtt_client = mqtt.Client('Raspberry')
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

print("Connecting to " + broker + " port: " + str(broker_port))
mqtt_client.connect(broker, broker_port)

publish_initial_parking_info()


# funzione per simulare il cambio di parcheggio "fisico", cioè dall'Arduino
def simulazione():
    while 1:
        a = input('\nParcheggio:\n')
        b = input('\nPostazione:\n')
        # simulo l'uscita di una macchina dal parcheggio
        mqtt_client.publish(f'parcheggio/parcheggio_{a}/postazione_{b}/timer', timer[int(a)-1][int(b)-1])
        print(f'Ho cambiato lo stato del parcheggio {a}, postazione {b} in 3 (terminato)')


t2 = threading.Thread(target=mqtt_client.loop_forever)
t2.start()
t3 = threading.Thread(target=simulazione)
t3.start()
