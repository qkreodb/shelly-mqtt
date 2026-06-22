import time
import json
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

# ================= [ 설정 정보 ] =================
BROKER = 'localhost'  # 젯슨 내부에서 돌아가는 MQTT 브로커 주소
PORT = 1883
COLLECTOR_CLIENT_ID = 'ds_safer_collector'

# 1. 쉘리 기기로부터 데이터를 받아오는 원본 토픽 (구독용)
SHELLY_TOPIC_TEMP = "sensors/status/temperature:0"
SHELLY_TOPIC_HUMI = "sensors/status/humidity:0"

# 2. [가공 완료] 최종 하드웨어 서버로 넘겨줄 타겟 명세 (토픽 규칙)
SENSOR_ID = "shelly-ht-001"
SENSOR_TYPE = "temp_humidity"
TELEMETRY_TOPIC = f"sensors/{SENSOR_ID}/telemetry"
STATUS_TOPIC = f"sensors/{SENSOR_ID}/status"
# =================================================

# 센서 데이터 일시 저장을 위한 캐시 변수
cached_data = {
    "temp": None,
    "humid": None
}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[성공] 수집 모듈이 MQTT 브로커에 연결되었습니다.")
        # 쉘리 토픽 구독 시작
        client.subscribe(SHELLY_TOPIC_TEMP)
        client.subscribe(SHELLY_TOPIC_HUMI)
        print(f" -> 구독 중인 원본 토픽: {SHELLY_TOPIC_TEMP}, {SHELLY_TOPIC_HUMI}")
        
        # 연결 직후 하드웨어 서버측 토픽으로 온라인 상태 세션 선언 발송
        publish_hardware_status(client, is_online=True)
    else:
        print(f"[실패] 브로커 연결 실패, 에러 코드: {rc}")

def publish_hardware_status(client, is_online: bool):
    """
    보내주신 스크립트 명세에 맞춘 status 페이로드 가공 및 전송
    """
    status_payload = {
        "sensor_id": SENSOR_ID,
        "sensor_type": SENSOR_TYPE,
        "is_online": is_online
    }
    client.publish(STATUS_TOPIC, json.dumps(status_payload), qos=1, retain=False)
    print(f"📡 [상태 전송] 토픽: {STATUS_TOPIC} | 페이로드: {status_payload}")

def process_and_publish_telemetry(client):
    """
    보내주신 스크립트 명세에 맞춘 telemetry 페이로드 가공 및 전송
    """
    # 온도와 습도 중 하나라도 아직 안 받아와졌다면 전송 보류
    if cached_data["temp"] is None or cached_data["humid"] is None:
        return

    telemetry_payload = {
        "sensor_id": SENSOR_ID,
        "sensor_type": SENSOR_TYPE,
        "temp": cached_data["temp"],
        "humid": cached_data["humid"]
    }
    
    # 가공된 토픽과 JSON 페이로드로 최종 발행
    client.publish(TELEMETRY_TOPIC, json.dumps(telemetry_payload), qos=1, retain=False)
    print(f"📊 [데이터 가공 완료 전송] 토픽: {TELEMETRY_TOPIC} | 페이로드: {telemetry_payload}")

def on_message(client, userdata, msg):
    topic = msg.topic
    raw_payload = msg.payload.decode('utf-8')
    
    try:
        data = json.loads(raw_payload)
        
        # 1. 원본 온도 토픽 패킷이 들어온 경우
        if topic == SHELLY_TOPIC_TEMP:
            temp_c = data.get("tC")
            if temp_c is not None:
                cached_data["temp"] = temp_c
                # 온도 수신 시 상태 최신화 겸 텔레메트리 조합 체크 및 전송
                publish_hardware_status(client, is_online=True)
                process_and_publish_telemetry(client)
                
        # 2. 원본 습도 토픽 패킷이 들어온 경우
        elif topic == SHELLY_TOPIC_HUMI:
            humidity = data.get("rh")
            if humidity is not None:
                cached_data["humid"] = humidity
                # 습도 수신 시 상태 최신화 겸 텔레메트리 조합 체크 및 전송
                publish_hardware_status(client, is_online=True)
                process_and_publish_telemetry(client)
                
    except json.JSONDecodeError:
        print(f"[경고] 깨진 JSON 수신: {raw_payload}")

def run():
    client = mqtt_client.Client(CallbackAPIVersion.VERSION2, COLLECTOR_CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        # 종료 시 시스템다운을 알리기 위한 오프라인 브로드캐스트
        print("\n[알림] 수집 모듈을 안전하게 종료합니다.")
        try:
            publish_hardware_status(client, is_online=False)
        except:
            pass
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == '__main__':
    run()
