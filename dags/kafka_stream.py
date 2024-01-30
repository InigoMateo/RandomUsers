import logging
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'inigo',
    'start_date': datetime(2024, 1, 28, 12, 00)
}


def get_data():
    import requests

    # Getting the response form the url
    res = requests.get('https://randomuser.me/api/')
    # Parsing the response to a json fomrat
    res = res.json()
    # Getting the first element of the array
    res = res['results'][0]

    return res


def format_data(res):
    data = {}
    # Data definition to parse the json response
    location = res['location']
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = (f"{str(location['street']['number'])} {location['street']['name']}"
                       f"{location['city']}, {location['state']}, {location['country']}")
    data['postcode'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

    return data


def stream_data():
    import json
    from kafka import KafkaProducer
    import time
    import logging

    # print(json.dumps(res, indent=3))

    # Initialize KafkaProducer
    producer = KafkaProducer(bootstrap_servers=['broker:29092'], max_block_ms=5000)

    curr_time = time.time()

    while True:
        if time.time() > curr_time + 60:  # 1 minute
            # Once the condition is true it breaks out of while loop
            break
        try:
            res = get_data()
            res = format_data(res)

            # Send message to broker listener
            producer.send('users_created', json.dumps(res).encode('utf-8'))
        except Exception as e:
            logging.error(f'An error occured: {e}')
            continue


with DAG('user_automation',
         default_args=default_args,
         # Schedule interval can be set to '@hourly', '@daily', '@weekly', '@monthly', '@yearly'
         schedule='@daily',
         catchup=False) as dag:
    streaming_task = PythonOperator(
        task_id='stream_data_from_api',
        python_callable=stream_data
    )

stream_data();
