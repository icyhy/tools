import qrcode
import io
import base64
import socket

def generate_qr_base64(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def get_server_url(port: int = 8000) -> str:
    """
    获取服务器的访问URL，优先使用局域网IP地址而不是localhost
    这样手机扫码后可以正常访问
    
    Args:
        port: 服务端口号，默认8000
        
    Returns:
        服务器URL，格式：http://IP:PORT
    """
    try:
        # 尝试获取本机局域网IP地址
        # 创建一个UDP socket连接外部地址来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:{port}"
    except Exception:
        # 如果获取失败，使用默认IP（可以通过环境变量配置）
        import os
        default_ip = os.getenv("SERVER_IP", "192.168.1.34")
        return f"http://{default_ip}:{port}"
