import csv
import json
import random
from datetime import datetime, timedelta

def generate_data():
    # 100명의 가상 유저
    users = [f"U{str(i).zfill(4)}" for i in range(1, 101)]
    statuses = ["COMPLETED", "COMPLETED", "COMPLETED", "REFUNDED", "FAILED", "PENDING", "UNKNOWN_STATUS"]
    
    base_time = datetime(2023, 10, 1)

    print("생성 중: orders.csv (주문 데이터 - 결측치 및 포맷 불일치 포함)...")
    with open('raw_data/orders.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['order_id', 'user_id', 'order_timestamp', 'amount', 'status'])
        
        for i in range(1, 501):
            order_id = f"ORD-{i}"
            user_id = random.choice(users)
            
            # [의도적인 오류] 5% 확률로 날짜 포맷을 다르게 생성 (YYYY/MM/DD HH:MM)
            if random.random() < 0.05:
                order_time = (base_time + timedelta(minutes=random.randint(0, 43200))).strftime("%Y/%m/%d %H:%M")
            else:
                order_time = (base_time + timedelta(minutes=random.randint(0, 43200))).isoformat()
                
            # [의도적인 오류] 5% 확률로 금액을 마이너스, 0, 또는 빈 값으로 설정
            if random.random() < 0.05:
                amount = random.choice([-10000, 0, ""])
            else:
                amount = random.randint(10, 500) * 100
                
            status = random.choice(statuses)
            writer.writerow([order_id, user_id, order_time, amount, status])

    print("생성 중: user_logs.jsonl (유저 행동 로그 - 불완전한 JSON 데이터 포함)...")
    events = ["login", "view_item", "add_to_cart", "checkout"]
    devices = ["iOS", "Android", "Web"]
    
    with open('raw_data/user_logs.jsonl', 'w') as f:
        for i in range(1, 1001):
            user_id = random.choice(users)
            event = random.choice(events)
            log_time = (base_time + timedelta(minutes=random.randint(0, 43200))).isoformat()
            
            log_data = {
                "log_id": f"LOG-{i}",
                "user_id": user_id,
                "event_time": log_time,
                "event_name": event,
                "event_properties": {
                    "device": random.choice(devices),
                    "ip_address": f"192.168.1.{random.randint(1,255)}"
                }
            }
            # [의도적인 오류] 10% 확률로 event_properties를 통째로 누락
            if random.random() < 0.1:
                del log_data["event_properties"]
                
            f.write(json.dumps(log_data) + '\n')
            
    print("성공! 가짜 데이터가 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    generate_data()
