import time
from paho.mqtt import client as mqtt_client

# --- 설정 정보 ---
BROKER = 'localhost'  # 젯슨 자체를 브로커로 쓸 경우 localhost, 다르면 브로커 IP 입력
PORT = 1883
CLIENT_ID = 'jetson_mqtt_tester'

# 쉘리 기기의 토픽 정보
TOPIC_TEMP = "shellyhtg3-80b54e358c18/status/temperature:0"
TOPIC_HUMI = "shellyhtg3-80b54e358c18/status/humidity:0"

# 브로커 연결 성공 시 실행되는 함수
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[성공] MQTT 브로커에 연결되었습니다!")
        # 연결이 성공하면 토픽 2개를 구독(Subscribe)합니다.
        client.subscribe(TOPIC_TEMP)
        client.subscribe(TOPIC_HUMI)
        print(f"구독 시작:\n - {TOPIC_TEMP}\n - {TOPIC_HUMI}\n")
        print("쉘리 기기 로부터 데이터를 기다리는 중... (Ctrl+C로 종료)\n")
    else:
        print(f"[실패] 브로커 연결 실패, 에러 코드: {rc}")

# 메시지(데이터)를 받았을 때 실행되는 함수
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8')
    
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 수신 데이터 발생!")
    if "temperature" in topic:
        print(f" 🌡️ 온도 토픽 데이터: {payload}")
    elif "humidity" in topic:
        print(f" 💧 습도 토픽 데이터: {payload}")
    print("-" * 40)

def run():
    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # 브로커 연결 시도
        client.connect(BROKER, PORT, keepalive=60)
        # 네트워크 루프 시작 (메시지를 계속 기다림)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n테스트 서버를 종료합니다.")
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == '__main__':
    run()