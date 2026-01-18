from fastapi.testclient import TestClient
from app.main import app
from app.models import Event, Base
from app.database import SessionLocal, engine
import sys

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Reset DB for testing
db = SessionLocal()
try:
    db.query(Event).delete()
    db.commit()
except Exception:
    db.rollback()
finally:
    db.close()

client = TestClient(app)

def test_requirements():
    print("开始功能验证 (Verifying requirements)...")
    
    # 1. 验证大屏首页 (Display Page)
    print("- [1/6] 验证大屏首页 (Display Page)... ", end="")
    response = client.get("/")
    assert response.status_code == 200
    assert "大屏" in response.text or "互动系统" in response.text
    print("✅ Pass")

    # 2. 验证签到页面 (Signin Page)
    print("- [2/6] 验证签到页面 (Signin Page)... ", end="")
    response = client.get("/signin")
    assert response.status_code == 200
    assert "签到" in response.text
    print("✅ Pass")

    # 3. 验证参会人签到 (User Signin)
    print("- [3/6] 验证参会人签到 (User Signin)... ", end="")
    response = client.post("/api/signin", data={
        "name": "TestUser",
        "role": "user"
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/mobile/home"
    assert "session_token" in response.cookies
    print("✅ Pass")

    # 4. 验证主持人签到 - 密码错误 (Host Signin Fail)
    print("- [4/6] 验证主持人签到失败情况 (Host Signin Fail)... ", end="")
    response = client.post("/api/signin", data={
        "name": "HostUser",
        "role": "host",
        "host_password": "wrongpassword"
    })
    assert response.status_code == 200
    assert "主持人密码错误" in response.text
    print("✅ Pass")

    # 5. 验证主持人签到 - 密码正确 (Host Signin Success)
    print("- [5/6] 验证主持人签到成功情况 (Host Signin Success)... ", end="")
    response = client.post("/api/signin", data={
        "name": "HostUser",
        "role": "host",
        "host_password": "admin123"
    }, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/mobile/host"
    print("✅ Pass")
    
    # 6. 验证管理员页面 (Admin Page)
    print("- [6/6] 验证管理员页面 (Admin Page)... ", end="")
    response = client.get("/admin")
    assert response.status_code == 200
    assert "培训配置管理" in response.text
    print("✅ Pass")

    print("\n所有功能验证通过! (All requirements verified)")

if __name__ == "__main__":
    try:
        test_requirements()
    except AssertionError as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        sys.exit(1)
