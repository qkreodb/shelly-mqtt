# shelly-mqtt
쉘리 온습도 센서 &lt;-> 서버 간 MQTT 통신

# 사전 작업
pip install paho-mqtt

# 기존 모듈은 켜두고 새로운 모듈 실행 후
mosquitto_sub -h localhost -p 1883 -t "sensors/shelly-ht-001/telemetry"
-> 정제된 JSON 데이터 확인
