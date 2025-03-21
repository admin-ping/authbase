# coding:utf-8
# by 川普
from scapy.all import *
import time
import hashlib

# 配置区域
SERVER_IP = '192.168.1.173'
KNOCK_SEQUENCE = [
    (4214, 'TCP'),
    (24161, 'UDP'),
    (6325, 'TCP'),
    (54221,'UDP')
]


def send_knock():
    # 密码处理
    password = hashlib.md5(str(input("请输入连接密码：\n")).strip().encode()).hexdigest().encode()  # 转换为bytes

    for i, (port, proto) in enumerate(KNOCK_SEQUENCE):
        try:
            if proto == 'TCP':
                # TCP协议处理
                if i == len(KNOCK_SEQUENCE) - 1:
                    pkt = IP(dst=SERVER_IP) / TCP(dport=port, flags="PA") / Raw(load=password)
                else:
                    pkt = IP(dst=SERVER_IP) / TCP(dport=port, flags="S")

            elif proto == 'UDP':
                # 修复UDP协议处理
                payload = password if i == len(KNOCK_SEQUENCE) - 1 else b'google.com'
                pkt = IP(dst=SERVER_IP) / UDP(dport=port) / Raw(load=payload)  # 三层结构

            send(pkt, verbose=0)
            print(f"[+] {proto}端口 {port} 敲门成功")
            time.sleep(0.2)

        except Exception as e:
            print(f"[-] {proto}/{port} 敲门失败: {str(e)}")
            break  # 失败时终止后续操作


if __name__ == "__main__":
    send_knock()
    print("[+] 敲门序列完成")
