import subprocess
import sys
import os

def install_requirements():
    print("正在检查并安装依赖 (Installing dependencies)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成 (Dependencies installed).")
    except subprocess.CalledProcessError:
        print("依赖安装失败，请检查网络或权限 (Failed to install dependencies).")
        sys.exit(1)

def run_server():
    print("正在启动服务 (Starting server)...")
    print("大屏幕入口 (Display): http://localhost:8000/")
    print("管理员入口 (Admin): http://localhost:8000/admin")
    print("手机签到 (Mobile): http://localhost:8000/signin")
    
    try:
        import uvicorn
        # reload=True works best when run as a module or with string import
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("Uvicorn not found after installation? Please run 'pip install uvicorn'")

if __name__ == "__main__":
    # Simple check for key packages
    missing_packages = []
    try:
        import fastapi
    except ImportError:
        missing_packages.append("fastapi")
        
    try:
        import uvicorn
    except ImportError:
        missing_packages.append("uvicorn")
        
    try:
        import qrcode
    except ImportError:
        missing_packages.append("qrcode")

    if missing_packages:
        print(f"缺少依赖包: {', '.join(missing_packages)}")
        install_requirements()
    
    # Run
    run_server()
