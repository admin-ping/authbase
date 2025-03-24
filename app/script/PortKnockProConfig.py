# coding:utf-8
from scapy.all import *
import time
import hashlib
import sys
import ctypes
import traceback
import logging
from getpass import getpass
import os

# 配置Scapy日志级别
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


def check_admin():
    """检查Windows管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def parse_portlist(portlist_str):
    """解析端口列表字符串为(端口, 协议)元组列表"""
    sequence = []
    # 移除引号
    portlist_str = portlist_str.strip('"')
    for item in portlist_str.split(','):
        item = item.strip()
        if not item:
            continue
        try:
            port, proto = item.split(':', 1)
            port = int(port)
            if not (1 <= port <= 65535):
                raise ValueError(f"端口 {port} 超出有效范围(1-65535)")
            if proto.upper() not in ("TCP", "UDP"):
                raise ValueError(f"不支持的协议类型: {proto}")
            sequence.append((port, proto.upper()))
        except ValueError as e:
            raise ValueError(f"无效的端口格式 '{item}'，应使用 端口:协议 格式") from e
    if not sequence:
        raise ValueError("敲门序列不能为空")
    return sequence


def build_packet(proto, server_ip, port, payload):
    """构建协议栈"""
    ip_layer = IP(
        dst=server_ip,
        proto=6 if proto == "TCP" else 17,
        id=RandShort(),
        flags="DF"
    )

    if proto == "TCP":
        transport_layer = TCP(
            dport=port,
            sport=RandShort(),
            flags="PA" if payload else "S",
            seq=RandInt(),
            window=2048
        )
    else:
        transport_layer = UDP(
            dport=port,
            sport=RandShort()
        )

    return ip_layer / transport_layer / Raw(load=payload) if payload else ip_layer / transport_layer


def send_knock(server_ip, knock_sequence, password_hash):
    """执行端口敲门序列"""
    try:
        for i, (port, proto) in enumerate(knock_sequence):
            try:
                # 构造数据包
                is_last = (i == len(knock_sequence) - 1)
                payload = password_hash if is_last else (b"" if proto == "TCP" else b"knock_sequence")

                pkt = build_packet(proto, server_ip, port, payload if is_last else None)

                # 发送数据包
                send(pkt, verbose=0)
                print(f"[✓] {proto} 端口 {port} 敲门成功")
                time.sleep(0.3)

            except Exception as e:
                print(f"\n[×] {proto}/{port} 失败: {str(e)}")
                print("可能原因排查:")
                print("1. 检查Npcap/WinPcap驱动安装")
                print("2. 确认防火墙允许原始套接字")
                print("3. 验证目标IP和端口配置")
                return False
        return True
    except KeyboardInterrupt:
        print("\n[!] 用户中止操作")
        return False


def read_config():
    """从start.txt读取配置"""
    try:
        # 获取程序运行时的实际路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是python脚本
            base_path = os.path.dirname(__file__)
            
        config_path = os.path.join(base_path, 'start.txt')
        if not os.path.exists(config_path):
            raise FileNotFoundError("找不到配置文件 start.txt")

        with open(config_path, 'r') as f:
            lines = f.readlines()

        if len(lines) < 2:
            raise ValueError("配置文件格式错误：需要目标IP和端口序列")

        host = lines[0].strip()
        portlist = lines[1].strip()

        return host, portlist
    except Exception as e:
        print(f"[!] 读取配置文件失败: {str(e)}")
        sys.exit(1)


def main():
    try:
        # 检查Windows管理员权限
        if sys.platform.startswith('win') and not check_admin():
            print("[!] 请以管理员权限运行此程序")
            input("按回车键退出...")
            sys.exit(1)

        # 读取配置文件
        print("[*] 正在读取配置文件...")
        host, portlist = read_config()
        print(f"[✓] 目标主机: {host}")
        print(f"[✓] 端口序列: {portlist}")

        # 解析敲门序列
        try:
            knock_sequence = parse_portlist(portlist)
        except ValueError as e:
            print(f"[!] 配置错误: {str(e)}")
            sys.exit(2)

        # 密码处理
        try:
            print("\n为了安全考虑，输入的密码将不会显示在屏幕上")
            passwd = getpass("请输入认证密码(明文)：").strip()
            if not passwd:
                raise ValueError("密码不能为空")
            # 将明文转换为MD5哈希
            password_hash = hashlib.md5(passwd.encode()).hexdigest().encode()
        except Exception as e:
            print(f"[!] 密码处理失败: {str(e)}")
            sys.exit(3)

        # 执行敲门协议
        print(f"\n🚪 开始执行 {len(knock_sequence)} 步敲门协议...")
        success = send_knock(host, knock_sequence, password_hash)

        # 结果处理
        if success:
            print("\n[✓] 所有敲门包已发送，请检查服务端状态")
        else:
            print("\n[×] 敲门流程中断")

        # 安全退出
        try:
            input("\n按回车键退出...")
        except KeyboardInterrupt:
            print("\n[!] 用户取消操作")

    except KeyboardInterrupt:
        print("\n[!] 用户中止程序")
    except Exception as e:
        print(f"\n[×] 发生未处理异常: {str(e)}")
        traceback.print_exc()
        sys.exit(99)


if __name__ == "__main__":
    main()