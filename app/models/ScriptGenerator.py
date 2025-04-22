# coding:utf-8
# by 川普

import os
import re
import shutil
from tempfile import NamedTemporaryFile, mkdtemp
from zipfile import ZipFile

class ScriptGenerator:
    """客户端脚本生成器
    
    用于生成不同版本的端口敲门客户端脚本，支持Python、EXE和Bash版本。
    可以根据用户提供的参数动态替换脚本中的配置。
    
    Attributes:
        SCRIPT_DIR (str): 脚本文件所在目录
        PYTHON_TEMPLATE (str): Python版本脚本模板路径
        EXE_TEMPLATE (str): EXE版本程序路径
        BASH_TEMPLATE (str): Bash版本脚本模板路径
        START_TEMPLATE (str): EXE启动配置模板路径
    """
    
    def __init__(self):
        self.SCRIPT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'script')
        self.PYTHON_TEMPLATE = os.path.join(self.SCRIPT_DIR, 'client.py')
        self.EXE_TEMPLATE = os.path.join(self.SCRIPT_DIR, 'PortKnockProConfig.exe')
        self.BASH_TEMPLATE = os.path.join(self.SCRIPT_DIR, 'client.sh')
        self.START_TEMPLATE = os.path.join(self.SCRIPT_DIR, 'start.txt')
    
    def _format_port_sequence(self, port_sequence, script_type='python'):
        """格式化端口序列为不同脚本类型需要的格式
        
        Args:
            port_sequence (str): 原始端口序列字符串，格式如 "1201:TCP,2301:UDP"
            script_type (str): 脚本类型，可选值：python, exe, bash
            
        Returns:
            str: 格式化后的端口序列字符串
        """
        if script_type == 'python':
            # Python格式: [(port, 'PROTO'), ...]
            pairs = [f"({port}, '{proto}')" for port, proto in 
                    [item.split(':') for item in port_sequence.split(',')]]
            return '[\n    ' + ',\n    '.join(pairs) + '\n]'
        elif script_type == 'exe':
            # EXE格式: port1:PROTO,port2:PROTO
            return port_sequence
        else:  # bash
            # Bash格式: "port proto"
            pairs = [f'"{port} {proto.lower()}"' for port, proto in 
                    [item.split(':') for item in port_sequence.split(',')]]
            return '(' + ' '.join(pairs) + ')'
    
    def generate_python_script(self, host, port_sequence):
        """生成Python版本的客户端脚本
        
        Args:
            host (str): 目标服务器IP地址
            port_sequence (str): 端口序列
            
        Returns:
            str: 生成的临时文件路径
        """
        with open(self.PYTHON_TEMPLATE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置参数
        content = re.sub(
            r'SERVER_IP = .*\n',
            f"SERVER_IP = '{host}'\n",
            content
        )
        content = re.sub(
            r'KNOCK_SEQUENCE = \[.*?\]',
            f"KNOCK_SEQUENCE = {self._format_port_sequence(port_sequence)}",
            content,
            flags=re.DOTALL
        )
        
        # 创建临时文件
        temp_file = NamedTemporaryFile(delete=False, suffix='.py')
        with open(temp_file.name, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return temp_file.name
    
    def generate_exe_package(self, host, port_sequence):
        """生成EXE版本的客户端程序包
        
        Args:
            host (str): 目标服务器IP地址
            port_sequence (str): 端口序列
            
        Returns:
            str: 生成的ZIP文件路径
        """
        # 创建临时目录
        temp_dir = mkdtemp()
        
        # 复制EXE文件
        exe_path = os.path.join(temp_dir, 'PortKnockProConfig.exe')
        shutil.copy2(self.EXE_TEMPLATE, exe_path)
        
        # 复制说明文件
        instructions_path = os.path.join(temp_dir, 'instructions.txt')
        shutil.copy2(os.path.join(self.SCRIPT_DIR, 'instructions.txt'), instructions_path)
        
        # 生成启动配置文件
        start_content = f'{host}\n"{port_sequence}"'
        
        start_path = os.path.join(temp_dir, 'start.txt')
        with open(start_path, 'w', encoding='utf-8') as f:
            f.write(start_content)
        
        # 创建ZIP文件
        zip_path = os.path.join(temp_dir, 'knockclient_exe.zip')
        with ZipFile(zip_path, 'w') as zipf:
            zipf.write(exe_path, os.path.basename(exe_path))
            zipf.write(instructions_path, os.path.basename(instructions_path))
            zipf.write(start_path, os.path.basename(start_path))
        
        return zip_path
    
    def generate_bash_script(self, host, port_sequence):
        """生成Bash版本的客户端脚本
        
        Args:
            host (str): 目标服务器IP地址
            port_sequence (str): 端口序列
            
        Returns:
            str: 生成的临时文件路径
        """
        with open(self.BASH_TEMPLATE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置参数
        content = re.sub(
            r'SERVER_IP=.*\n',
            f"SERVER_IP='{host}'\n",
            content
        )
        content = re.sub(
            r'KNOCK_SEQUENCE=\(.*?\)',
            f"KNOCK_SEQUENCE={self._format_port_sequence(port_sequence, 'bash')}",
            content,
            flags=re.DOTALL
        )
        
        # 创建临时文件
        temp_file = NamedTemporaryFile(delete=False, suffix='.sh')
        with open(temp_file.name, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return temp_file.name