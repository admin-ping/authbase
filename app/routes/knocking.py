# coding:utf-8
"""
端口敲门认证管理模块

该模块提供了端口敲门认证规则的管理接口，包括添加、删除和查询规则。
端口敲门是一种通过按特定顺序访问一系列端口来获取访问权限的安全机制。

主要功能：
- 添加新的敲门规则
- 删除现有规则
- 查询所有规则
- 管理规则进程的生命周期

"""

# 导入所需的模块和依赖
from .. import db
from ..base import base
from flask import request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
import subprocess
import os
import psutil
import logging
import hashlib
import signal
from ..models.KnockingRule import KnockingRule
from ..models.ScriptGenerator import ScriptGenerator
from .. import permission

# 进程信息存储路径
PID_FILE_DIR = '/var/run/authbase_knocking/'  # 存储规则进程PID的目录
LOG_FILE = '/var/log/authbase/knocking.log'   # 日志文件路径

# 确保PID文件目录和日志目录存在，并设置正确的权限
def ensure_directories():
    """确保必要的目录存在并具有正确的权限
    
    该函数负责创建和配置端口敲门服务所需的目录结构，包括：
    1. PID文件存储目录 (/var/run/authbase_knocking/)
    2. 日志文件目录 (/var/log/authbase/)
    
    目录权限设置：
    - PID目录: 755 (用户完全访问，组和其他用户只读和执行)
    - 日志文件: 644 (用户读写，组和其他用户只读)
    
    Raises:
        OSError: 当目录创建或权限设置失败时抛出
        Exception: 其他未预期的错误
    """
    try:
        # 创建PID文件目录
        if not os.path.exists(PID_FILE_DIR):
            os.makedirs(PID_FILE_DIR, mode=0o755, exist_ok=True)
        
        # 创建日志目录
        log_dir = os.path.dirname(LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o755, exist_ok=True)
            
        # 设置日志文件权限
        if not os.path.exists(LOG_FILE):
            open(LOG_FILE, 'a').close()
        os.chmod(LOG_FILE, 0o644)
        
    except Exception as e:
        logging.error(f"创建目录失败: {str(e)}")
        raise

# 初始化目录
ensure_directories()


@base.route('/addrules', methods=['POST'])
@login_required
@permission('monitor:knocking:add')
def add_knocking_rule():
    """
    添加敲门规则
    
    创建新的端口敲门认证规则，并启动对应的监听进程。规则创建后会立即生效。
    每个规则包含端口序列、目标端口、时间窗口和认证密码等参数。
    
    Json Parameters:
        port_sequence (str): 端口序列，格式为"端口:协议,端口:协议,..."，例如"1201:TCP,2301:UDP,3401:TCP"
        target_port (int): 认证成功后开放的目标端口
        time_window (int): 完成端口序列的最大等待时间（秒）
        timeout (int): 认证成功后规则的有效期（秒）
        password (str): 认证密码，将被安全哈希存储
        remark (str, optional): 规则说明备注
        
    Returns:
        JSON响应：
        - 成功：{"status": "success", "pid": 进程ID, "command": 执行的命令}
        - 失败：{"error": 错误信息}
        
    Status Codes:
        201: 规则创建成功
        400: 请求参数缺失
        500: 服务器内部错误
    """
    data = request.get_json()

    # 参数映射
    mapped_data = {
        'port_sequence': data.get('portSequence'),
        'target_port': data.get('targetPort'),
        'time_window': data.get('timeWindow'),
        'timeout': data.get('timeout'),
        'password': hashlib.md5(data.get('password', '').encode('utf-8')).hexdigest()
    }

    # 参数验证
    required_fields = ['portSequence', 'targetPort', 'timeWindow', 'timeout', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # 生成安全密码
        # hashed_pwd = generate_password_hash(data['password'])

        # 生成规则ID（基于端口序列和目标端口）
        rule_str = f"{mapped_data['port_sequence'].replace(':', '_').replace(',', '-')}_{mapped_data['target_port']}"
        rule_id = hashlib.md5(rule_str.encode('utf-8')).hexdigest()

        # 创建数据库记录
        rule = KnockingRule(
            id=rule_id,
            port_sequence=mapped_data['port_sequence'],
            target_port=mapped_data['target_port'],
            time_window=mapped_data['time_window'],
            timeout=mapped_data['timeout'],
            password_hash=mapped_data['password'],
            create_by=current_user.LOGINNAME,
            remark=data.get('remark')
        )
        db.session.add(rule)

        # 记录操作日志（带用户信息）
        logging.info(f"用户 {current_user.LOGINNAME} 添加敲门规则：{data}")

        # 构造命令
        cmd = [
            'sudo',  # 需要root权限
            'python3',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'knocking_cmd.py'),
            '-pl', mapped_data['port_sequence'],
            '-p', str(mapped_data['target_port']),
            '-w', str(mapped_data['time_window']),
            '-t', str(mapped_data['timeout']),
            '-passwd', mapped_data['password']
        ]

        pid_file = os.path.join(PID_FILE_DIR, f"{rule_id}.pid")
        
        # 检查是否已有相同规则的进程在运行
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                process = psutil.Process(pid)
                # 如果进程存在且在运行，直接返回成功
                return jsonify({
                    "status": "success",
                    "message": "规则已在运行中",
                    "pid": pid
                }), 200
            except (psutil.NoSuchProcess, FileNotFoundError):
                # 如果进程不存在，删除过期的PID文件
                os.remove(pid_file)

        # 启动新进程
        process = subprocess.Popen(
            cmd,
            stdout=open(LOG_FILE, 'a'),
            stderr=subprocess.STDOUT,
            # 在Windows系统中使用CREATE_NEW_PROCESS_GROUP替代setsid
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # 记录PID
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))

        # 提交数据库事务
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '规则添加成功',
            'data': {
                'pid': process.pid,
                'command': ' '.join(cmd)
            }
        }), 201

    except Exception as e:
        # 回滚数据库事务
        db.session.rollback()
        logging.error(f"启动失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


def stop_knocking_service(pid_file=None):
    """停止运行中的服务
    
    停止指定的端口敲门认证服务进程，或者停止所有运行中的服务进程。
    该函数会尝试优雅地终止进程，并清理相关的PID文件。
    
    Args:
        pid_file: 特定规则的PID文件路径，如果为None则停止所有规则进程
        
    Note:
        - 如果指定的进程不存在，会清理对应的PID文件
        - 对于所有进程的停止操作都会记录到日志中
        - 进程终止使用SIGTERM信号，给予进程清理资源的机会
    """
    if pid_file and os.path.exists(pid_file):
        # 停止特定规则的进程
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())

        try:
            if os.name != 'nt':
                # Linux系统下使用kill命令发送SIGTERM信号
                os.kill(pid, signal.SIGTERM)
                logging.info(f"已发送SIGTERM信号到进程 {pid}")
            else:
                process = psutil.Process(pid)
                process.terminate()
            logging.info(f"已停止进程 {pid}")
        except (psutil.NoSuchProcess, ProcessLookupError):
            logging.warning(f"进程 {pid} 不存在")
            pass

        os.remove(pid_file)
    elif pid_file is None and os.path.exists(PID_FILE_DIR):
        # 停止所有规则进程
        for filename in os.listdir(PID_FILE_DIR):
            if filename.endswith('.pid'):
                pid_path = os.path.join(PID_FILE_DIR, filename)
                try:
                    with open(pid_path, 'r') as f:
                        pid = int(f.read().strip())
                    
                    try:
                        if os.name != 'nt':
                            # Linux系统下使用kill命令发送SIGTERM信号
                            os.kill(pid, signal.SIGTERM)
                            logging.info(f"已发送SIGTERM信号到进程 {pid}")
                        else:
                            process = psutil.Process(pid)
                            process.terminate()
                        logging.info(f"已停止进程 {pid}")
                    except (psutil.NoSuchProcess, ProcessLookupError):
                        pass
                    
                    os.remove(pid_path)
                except Exception as e:
                    logging.error(f"停止进程时出错: {str(e)}")
                    continue

@base.route('/rules/<rule_id>', methods=['DELETE'])
@login_required
@permission('monitor:knocking:delete')
def delete_knocking_rule(rule_id):
    """删除敲门规则
    
    删除指定的端口敲门规则，包括停止对应的监听进程和清理数据库记录。
    该操作需要登录权限，并且会记录操作日志。
    
    Args:
        rule_id: 要删除的规则ID
        
    Returns:
        JSON响应：
        - 成功：{"status": "success", "message": "规则已删除"}
        - 失败：{"error": 错误信息}
        
    Status Codes:
        200: 删除成功
        404: 规则不存在
        500: 服务器内部错误
    """
    try:
        # 查找并删除数据库记录
        rule = KnockingRule.query.get(rule_id)
        if rule:
            db.session.delete(rule)

        # 构造PID文件路径
        pid_file = os.path.join(PID_FILE_DIR, f"{rule_id}.pid")
        
        # 检查规则是否存在
        if not os.path.exists(pid_file):
            if not rule:
                return jsonify({
                    'code': 404,
                    'msg': '规则不存在'
                }), 404
            # 如果数据库记录存在但进程不存在，只删除数据库记录
            db.session.commit()
            return jsonify({
                'code': 200,
                'msg': '规则已删除'
            }), 200
            
        # 停止进程并删除PID文件
        stop_knocking_service(pid_file)
        
        # 记录操作日志
        logging.info(f"用户 {current_user.LOGINNAME} 删除敲门规则：{rule_id}")
        
        # 提交数据库事务
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'msg': '规则已删除'
        }), 200
    except Exception as e:
        # 回滚数据库事务
        db.session.rollback()
        logging.error(f"删除规则失败: {str(e)}")
        return jsonify({'code': 500, 'msg': str(e)}), 500

@base.route('/listrules', methods=['GET'])
@login_required
@permission('monitor:knocking:list')
def list_knocking_rules():
    """获取所有敲门规则列表
    
    获取系统中所有已配置的端口敲门规则。
    该接口需要登录权限，返回的规则信息包含完整的配置参数。
    
    Returns:
        JSON响应：
        - 成功：{"code": 200, "data": [...规则列表]}
            规则列表中每个规则包含：
            - id: 规则ID
            - port_sequence: 端口序列
            - target_port: 目标端口
            - time_window: 时间窗口
            - timeout: 超时时间
            - status: 规则状态
            - create_time: 创建时间
            等完整信息
        - 失败：{"error": 错误信息}
        
    Status Codes:
        200: 获取成功
        500: 服务器内部错误
    """
    try:
        rules = KnockingRule.query.all()
        return jsonify({
            'code': 200,
            'msg': '获取成功',
            'data': [rule.to_json() for rule in rules]
        })
    except Exception as e:
        logging.error(f"获取规则列表失败: {str(e)}")
        return jsonify({'code': 500, 'msg': str(e)}), 500


@base.route('/rules/<rule_id>', methods=['PUT'])
@login_required
@permission('monitor:knocking:edit')
def update_knocking_rule(rule_id):
    """修改敲门规则
    
    修改指定的端口敲门规则，包括更新规则参数和重启监听进程。
    该操作需要登录权限，并且会记录操作日志。
    
    Args:
        rule_id: 要修改的规则ID
        
    Json Parameters:
        port_sequence (str): 端口序列，格式为"端口:协议,端口:协议,..."，例如"1201:TCP,2301:UDP,3401:TCP"
        target_port (int): 认证成功后开放的目标端口
        time_window (int): 完成端口序列的最大等待时间（秒）
        timeout (int): 认证成功后规则的有效期（秒）
        password (str): 认证密码，将被安全哈希存储
        remark (str, optional): 规则说明备注
        
    Returns:
        JSON响应：
        - 成功：{"code": 200, "msg": "规则修改成功", "data": {"pid": 进程ID}}
        - 失败：{"code": 错误码, "msg": 错误信息}
        
    Status Codes:
        200: 修改成功
        400: 请求参数缺失
        404: 规则不存在
        500: 服务器内部错误
    """
    data = request.get_json()
    
    # 参数映射和验证
    mapped_data = {
        'port_sequence': data.get('portSequence'),
        'target_port': data.get('targetPort'),
        'time_window': data.get('timeWindow'),
        'timeout': data.get('timeout'),
        'password': hashlib.md5(data.get('password', '').encode('utf-8')).hexdigest()
    }
    
    # 参数验证
    required_fields = ['portSequence', 'targetPort', 'timeWindow', 'timeout', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({
            'code': 400,
            'msg': '缺少必要的参数'
        }), 400

    try:
        # 查找规则
        rule = KnockingRule.query.get(rule_id)
        if not rule:
            return jsonify({
                'code': 404,
                'msg': '规则不存在'
            }), 404

        # 更新规则信息
        rule.port_sequence = mapped_data['port_sequence']
        rule.target_port = mapped_data['target_port']
        rule.time_window = mapped_data['time_window']
        rule.timeout = mapped_data['timeout']
        rule.password_hash = mapped_data['password']
        rule.update_by = current_user.LOGINNAME
        if 'remark' in data:
            rule.remark = data['remark']

        # 构造PID文件路径
        pid_file = os.path.join(PID_FILE_DIR, f"{rule_id}.pid")
        
        # 停止原有进程
        if os.path.exists(pid_file):
            stop_knocking_service(pid_file)

        # 构造新的命令
        cmd = [
            'sudo',
            'python3',
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models', 'knocking_cmd.py'),
            '-pl', mapped_data['port_sequence'],
            '-p', str(mapped_data['target_port']),
            '-w', str(mapped_data['time_window']),
            '-t', str(mapped_data['timeout']),
            '-passwd', mapped_data['password']
        ]

        # 启动新进程
        process = subprocess.Popen(
            cmd,
            stdout=open(LOG_FILE, 'a'),
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # 记录新的PID
        with open(pid_file, 'w') as f:
            f.write(str(process.pid))

        # 记录操作日志
        logging.info(f"用户 {current_user.LOGINNAME} 修改敲门规则：{rule_id}")
        
        # 提交数据库事务
        db.session.commit()

        return jsonify({
            'code': 200,
            'msg': '规则修改成功',
            'data': {
                'pid': process.pid
            }
        })

    except Exception as e:
        # 回滚数据库事务
        db.session.rollback()
        logging.error(f"修改规则失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': str(e)
        }), 500


@base.route('/script/<rule_id>/<script_type>', methods=['GET'])
@login_required
@permission('monitor:knocking:script')
def generate_client_script(rule_id, script_type):
    """生成端口敲门认证的客户端脚本
    
    根据指定的规则ID和脚本类型生成相应的客户端脚本。支持生成多种类型的客户端脚本，
    以方便不同环境下的使用。生成的脚本会包含完整的敲门序列和认证逻辑。
    
    功能特点：
    - 支持Python、EXE和Bash三种脚本格式
    - 自动获取服务器IP地址
    - 支持自定义目标主机地址
    - 生成的脚本包含完整的敲门认证逻辑
    
    Args:
        rule_id (str): 敲门规则ID，用于获取对应的端口序列配置
        script_type (str): 脚本类型，可选值：
            - python: 生成Python脚本，适合Python环境
            - exe: 生成Windows可执行文件，适合Windows环境
            - bash: 生成Shell脚本，适合Linux/Unix环境
    
    Query Parameters:
        host (str, optional): 目标服务器地址，如果不指定则自动获取服务器内网IP
    
    Returns:
        flask.Response: 文件下载响应，包含生成的客户端脚本
        
    Response Headers:
        Content-Type: application/octet-stream
        Content-Disposition: attachment; filename=<script_name>
    
    Status Codes:
        200: 脚本生成成功并开始下载
        400: 无效的脚本类型
        404: 指定的规则不存在
        500: 服务器内部错误
    
    Examples:
        >>> # 生成Python客户端脚本
        >>> GET /script/a1b2c3d4/python
        >>> # 生成指定目标主机的EXE客户端
        >>> GET /script/a1b2c3d4/exe?host=192.168.1.100
    
    Note:
        - 生成的脚本会自动包含认证所需的所有配置
        - 脚本的运行可能需要相应的环境和权限
        - 建议在安全的内网环境中使用
    """
    try:
        # 验证脚本类型
        if script_type not in ['python', 'exe', 'bash']:
            return jsonify({
                'code': 400,
                'msg': '无效的脚本类型'
            }), 400

        # 查找规则
        rule = KnockingRule.query.get(rule_id)
        if not rule:
            return jsonify({
                'code': 404,
                'msg': '规则不存在'
            }), 404

        # 获取服务器IP地址
        def get_internal_ip():
            import socket
            try:
                # 创建一个UDP socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # 连接一个外部地址（不需要真实连接）
                s.connect(("8.8.8.8", 80))
                # 获取本地socket的IP地址
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"

        # 优先使用请求参数中的host，如果没有则使用服务器内网IP
        host = request.args.get('host', get_internal_ip())


        # 初始化脚本生成器
        generator = ScriptGenerator()

        # 根据类型生成脚本
        if script_type == 'python':
            script_path = generator.generate_python_script(host, rule.port_sequence)
            filename = 'knockclient.py'
        elif script_type == 'exe':
            script_path = generator.generate_exe_package(host, rule.port_sequence)
            filename = 'knockclient_exe.zip'
        else:  # bash
            script_path = generator.generate_bash_script(host, rule.port_sequence)
            filename = 'knockclient.sh'

        # 记录操作日志
        logging.info(f"用户 {current_user.LOGINNAME} 下载了规则 {rule_id} 的 {script_type} 客户端脚本")

        # 返回文件
        return send_file(
            script_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logging.error(f"生成客户端脚本失败: {str(e)}")
        return jsonify({
            'code': 500,
            'msg': str(e)
        }), 500
