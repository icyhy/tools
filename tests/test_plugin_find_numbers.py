from fastapi.testclient import TestClient
from app.main import app
from app.models import Event, Participant
from app.database import SessionLocal, engine, Base
import sys
import uuid

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Reset DB for testing
db = SessionLocal()
try:
    db.query(Participant).delete()
    db.query(Event).delete()
    db.commit()
    
    # Create a default event
    event = Event(title="Test Event", host_password_hash="admin123", is_active=True)
    db.add(event)
    db.commit()
except Exception:
    db.rollback()
finally:
    db.close()

client = TestClient(app)

def test_find_numbers_flow():
    print("开始测试 '找数字规律' 插件流程 (Testing 'Find Numbers' plugin)...")
    
    # 1. 模拟主持人登录
    print("- [1/5] 模拟主持人登录... ", end="")
    host_response = client.post("/api/signin", data={
        "name": "HostUser",
        "role": "host",
        "host_password": "admin123"
    }, follow_redirects=False)
    
    if host_response.status_code != 302:
        print(f"\nHost Signin Failed: {host_response.text}")
        
    assert host_response.status_code == 302
    host_cookie = host_response.cookies.get("session_token")
    assert host_cookie is not None
    print(f"✅ Pass (Token: {host_cookie[:8]}...)")

    # 2. 模拟参会人登录
    print("- [2/5] 模拟参会人登录... ", end="")
    user_response = client.post("/api/signin", data={
        "name": "NormalUser",
        "role": "user"
    }, follow_redirects=False)
    
    assert user_response.status_code == 302
    user_cookie = user_response.cookies.get("session_token")
    assert user_cookie is not None
    print(f"✅ Pass (Token: {user_cookie[:8]}...)")
    
    # Clear cookies again to ensure clean state for explicit cookie passing
    client.cookies.clear()

    # 3. 主持人开启第 1 阶段
    print("- [3/5] 主持人开启第 1 阶段... ", end="")
    response = client.post(
        "/api/plugin/find_numbers/start",
        json={"stage": 1},
        cookies={"session_token": host_cookie}
    )
    if response.status_code != 200:
        # Debug DB
        db = SessionLocal()
        p = db.query(Participant).filter(Participant.session_token == host_cookie).first()
        print(f"\nResponse: {response.text}")
        print(f"Debug Participant: {p.name if p else 'None'}, Role: {p.role if p else 'None'}")
        db.close()
        
    assert response.status_code == 200
    assert response.json()["stage"] == 1
    print("✅ Pass")

    # 4. 参会人提交答案
    print("- [4/5] 参会人提交答案... ", end="")
    # 假设此时缺失数字包含 5, 10
    response = client.post(
        "/api/plugin/find_numbers/submit",
        json={"answers": [5, 10, 99]},
        cookies={"session_token": user_cookie}
    )
    assert response.status_code == 200
    result = response.json()
    assert "score" in result
    assert "correct" in result
    print(f"✅ Pass (Score: {result['score']})")

    # 5. 主持人停止游戏并查看结果
    print("- [5/5] 主持人停止游戏... ", end="")
    response = client.post(
        "/api/plugin/find_numbers/stop",
        cookies={"session_token": host_cookie}
    )
    assert response.status_code == 200
    end_data = response.json()
    # 这里的 status 是 stopped，具体结果通过 websocket 广播，
    # 但我们可以验证接口调用成功
    assert end_data["status"] == "stopped"
    print("✅ Pass")

    print("\n'找数字规律' 插件流程测试通过! (Plugin flow verified)")

if __name__ == "__main__":
    try:
        test_find_numbers_flow()
    except AssertionError as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        sys.exit(1)
