import pandas as pd
from streaming.kafka_streamer import produce_weather

def test_produce_weather(mocker):
    producer = mocker.Mock()
    mocker.patch('streaming.kafka_streamer.KafkaProducer', return_value=producer)
    df = pd.DataFrame([{'district': 'A', 'date': '2025-06-19', 'temp': 20, 'humidity': 50, 'wind_speed': 5}])
    produce_weather(df, topic='t', servers='s')
    producer.send.assert_called_once()
    producer.flush.assert_called_once()
    producer.close.assert_called_once()
