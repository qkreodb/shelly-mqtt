import time
import json  # JSON 페이로드 파싱을 위해 추가
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

# --- 설정 정보 ---
BROKER = 'localhost'  
PORT = 1883
CLIENT_ID = 'jetson_mqtt_tester'

# 쉘리 기기의 토픽 정보
TOPIC_TEMP = "shellyhtg3-80b54e358c18/status/temperature:0"
TOPIC_HUMI = "shellyhtg3-80b54e358c18/status/humidity:0"

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[성공] MQTT 브로커에 연결되었습니다!")
        client.subscribe(TOPIC_TEMP)
        client.subscribe(TOPIC_HUMI)
        print(f"구독 시작:\n - {TOPIC_TEMP}\n - {TOPIC_HUMI}\n")
        print("쉘리 기기로부터 데이터를 기다리는 중... (Ctrl+C로 종료)\n")
    else:
        print(f"[실패] 브로커 연결 실패, 에러 코드: {rc}")

# [수정] 수신된 JSON 페이로드를 파싱하여 깔끔하게 정리 출력하는 함수
def on_message(client, userdata, msg):
    topic = msg.topic
    raw_payload = msg.payload.decode('utf-8')
    
    try:
        # 문자열 형태의 JSON을 파이크 딕셔너리로 변환
        data = json.loads(raw_payload)
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        if "temperature" in topic:
            # 쉘리 온도 데이터 구조 예시: {"id": 0, "tC": 23.5, "tF": 74.3}
            temp_c = data.get("tC")
            if temp_c is not None:
                print(f"[{current_time}] 🌡️ 현재 온도: {temp_c} °C")
                print("-" * 40)
                
        elif "humidity" in topic:
            # 쉘리 습도 데이터 구조 예시: {"id": 0, "rh": 45.2}
            humidity = data.get("rh")
            if humidity is not None:
                print(f"[{current_time}] 💧 현재 습도: {humidity} %")
                print("-" * 40)
                
    except json.JSONDecodeError:
        # JSON 포맷이 아니거나 깨진 데이터가 올 경우 예외 처리
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 수신 데이터 파싱 실패 (JSON 아님)")
        print(f" 원본 데이터: {raw_payload}")
        print("-" * 40)

def run():
    client = mqtt_client.Client(CallbackAPIVersion.VERSION2, CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n테스트 서버를 종료합니다.")
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == '__main__':
    run()
