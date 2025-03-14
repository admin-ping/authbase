# coding:utf-8
# by 川普

"""
端口敲门认证服务端实现模块

该模块实现了一个增强型的端口敲门(Port Knocking)认证服务，通过监听特定端口序列的访问来动态管理防火墙规则。
主要特点：
- 支持TCP/UDP混合的敲门序列
- 基于时间窗口的序列验证
- 最终包密码验证机制
- 自动超时的防火墙规则管理
- 多客户端并发支持
- 详细的日志记录

工作流程：
1. 客户端按特定顺序访问预定义的端口序列
2. 服务端验证访问序列的正确性和时间窗口
3. 验证最后一个包中的密码
4. 通过验证后，临时开放目标端口访问权限
5. 在超时后自动关闭端口访问

使用方法：
    python knocking_cmd.py -pl "1201:TCP,2301:UDP,3401:TCP" -p 22 -passwd "secret" -w 10 -t 30

需要root权限运行。

作者: Trump
"""

from scapy.all import *
from threading import Lock, Thread
import time
import subprocess
from shlex import quote
import argparse
import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 开启调试模式

    # 控制台日志格式
    console_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    # 文件日志处理器（带轮转）
    file_handler = TimedRotatingFileHandler(
        filename='knocking_cmd.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )

    # 自定义文件名格式
    def custom_namer(default_name):
        base, ext = os.path.splitext(default_name)
        if '.' in base:
            main_part, date = base.rsplit('.', 1)
            return f"{main_part}-{date}.log"
        return default_name

    file_handler.namer = custom_namer
    file_formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


logger = setup_logging()


def parse_knock_sequence(seq_str):
    try:
        sequence = []
        for item in seq_str.split(','):
            port, proto = item.split(':')
            port = int(port.strip())
            proto = proto.strip().upper()
            if proto not in ('TCP', 'UDP'):
                raise ValueError
            sequence.append((port, proto))
        return sequence
    except:
        raise argparse.ArgumentTypeError("无效的敲门序列格式，示例：1201:TCP,2301:UDP,3401:TCP")


def parse_arguments():
    parser = argparse.ArgumentParser(description="增强型Port Knocking服务端")
    parser.add_argument('-pl', '--port-list',
                        type=parse_knock_sequence,
                        required=True,
                        help='敲门序列（格式：端口:协议,...）')
    parser.add_argument('-p', '--target-port',
                        type=int,
                        required=True,
                        help='目标开放端口')
    parser.add_argument('-passwd', '--password',
                        required=True,
                        help='最终包密码')
    parser.add_argument('-w', '--window',
                        type=int,
                        default=10,
                        help='时间窗口（秒）')
    parser.add_argument('-t', '--timeout',
                        type=int,
                        default=30,
                        help='规则有效期（秒）')
    parser.add_argument('-z', '--zone',
                        default='public',
                        help='防火墙区域')
    return parser.parse_args()


class KnockStateMachine:
    def __init__(self, args):
        self.args = args
        self.clients = {}
        self.lock = Lock()
        self.firewall_rules = set()

        # 生成BPF过滤器
        ports = {str(p[0]) for p in args.port_list}
        self.bpf_filter = f"(tcp or udp) and (dst port {' or '.join(ports)})"

        # 预加载密码
        self.expected_password = args.password.encode('utf-8')

    def process_packet(self, pkt):
        """
        数据包处理核心逻辑
        处理流程：
        1. 解析IP协议层基本信息
        2. 分离TCP/UDP协议头和载荷数据
        3. 验证端口序列顺序和时间窗口
        4. 在最终步骤进行密码验证
        5. 通过验证后添加临时防火墙规则
        """
        if not IP in pkt:
            return

        src_ip = pkt[IP].src
        current_time = time.time()
        proto, port, payload = None, None, b''

        # 协议解析逻辑（同时处理TCP和UDP协议）
        if TCP in pkt:
            proto = 'TCP'
            port = pkt[TCP].dport  # 目标端口号
            if Raw in pkt:
                payload = pkt[Raw].load  # 应用层载荷数据
        elif UDP in pkt:
            proto = 'UDP'
            port = pkt[UDP].dport
            if Raw in pkt:
                payload = pkt[Raw].load
        else:
            return

        with self.lock:
            # 调试日志：显示收到包的信息
            logger.debug(f"收到 {proto}/{port} 来自 {src_ip} 载荷长度：{len(payload)}")

            client = self.clients.get(src_ip)
            if not client:
                # 检查是否是第一个敲门包
                if len(self.args.port_list) > 0 and \
                        port == self.args.port_list[0][0] and \
                        proto == self.args.port_list[0][1]:
                    self.clients[src_ip] = {
                        'step': 1,
                        'start_time': current_time
                    }
                    logger.info(f"初始化客户端 {src_ip}")
                return
            else:
                # 检查时间窗口
                if current_time - client['start_time'] > self.args.window:
                    logger.warning(f"客户端 {src_ip} 超时")
                    del self.clients[src_ip]
                    return

                # 获取当前步骤期望值
                current_step = client['step']
                try:
                    expected_port, expected_proto = self.args.port_list[current_step]
                except IndexError:
                    logger.error(f"客户端 {src_ip} 步骤越界")
                    del self.clients[src_ip]
                    return

                # 协议/端口验证
                if port == expected_port and proto == expected_proto:
                    # 最终步骤密码验证
                    if current_step == len(self.args.port_list) - 1:
                        logger.debug(f"最终步骤验证 {src_ip} 载荷内容：{payload[:16]}...")
                        if payload != self.expected_password:
                            logger.warning(f"密码验证失败 {src_ip}")
                            del self.clients[src_ip]
                            return
                        logger.info(f"密码验证成功 {src_ip}")

                    # 更新步骤
                    client['step'] += 1
                    client['start_time'] = current_time

                    # 完成序列
                    if client['step'] == len(self.args.port_list):
                        self._activate_firewall(src_ip)
                        del self.clients[src_ip]
                else:
                    logger.warning(f"无效步骤 {src_ip} 期望 {expected_proto}/{expected_port}")
                    del self.clients[src_ip]

    def _activate_firewall(self, ip):
        """
        添加临时防火墙规则
        使用firewall-cmd创建富规则：
        firewall-cmd --zone=public --add-rich-rule=
            'rule family=ipv4 source address=IP port port=PORT protocol=tcp accept'
        """
        if (ip, self.args.target_port) in self.firewall_rules:
            return

        try:
            ip_escaped = quote(ip)
            port_escaped = quote(str(self.args.target_port))

            # 使用firewall-cmd添加富规则
            add_cmd = [
                'firewall-cmd',
                f'--zone={self.args.zone}',
                '--add-rich-rule',
                f'rule family="ipv4" source address="{ip_escaped}" '
                f'port port="{port_escaped}" protocol="tcp" accept'
            ]

            subprocess.run(add_cmd, check=True)
            self.firewall_rules.add((ip, self.args.target_port))
            logger.info(f"开放端口 {self.args.target_port} 给 {ip}")

            # 启动定时删除线程
            Thread(target=self._remove_firewall, args=(ip,)).start()
        except subprocess.CalledProcessError as e:
            logger.error(f"防火墙添加失败: {str(e)}")

    def _remove_firewall(self, ip):
        time.sleep(self.args.timeout)
        try:
            ip_escaped = quote(ip)
            port_escaped = quote(str(self.args.target_port))

            del_cmd = [
                'firewall-cmd',
                f'--zone={self.args.zone}',
                '--remove-rich-rule',
                f'rule family="ipv4" source address="{ip_escaped}" '
                f'port port="{port_escaped}" protocol="tcp" accept'
            ]

            subprocess.run(del_cmd, check=True)
            self.firewall_rules.discard((ip, self.args.target_port))
            logger.info(f"关闭 {ip} 对 {self.args.target_port}端口 的访问权限")
        except subprocess.CalledProcessError as e:
            logger.error(f"防火墙规则移除失败: {str(e)}")


def main():
    if os.geteuid() != 0:
        logger.error("需要root权限运行")
        sys.exit(1)

    args = parse_arguments()
    logger.info(f"""
    === 服务启动参数 ===
    敲门序列：{args.port_list}
    目标端口：{args.target_port}
    时间窗口：{args.window}秒
    规则有效期：{args.timeout}秒
    防火墙区域：{args.zone}
    ===================
    """)

    # 设置Scapy性能参数
    # conf.iface = "ens33"  # 指定监听网卡
    # conf.sniff_promisc = 0  # 关闭混杂模式

    fsm = KnockStateMachine(args)
    sniff(prn=fsm.process_packet,
          filter=fsm.bpf_filter,
          store=0,
          promisc=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("服务已手动停止")
        sys.exit(0)
    except Exception as e:
        logger.exception("致命错误:")
        sys.exit(1)



