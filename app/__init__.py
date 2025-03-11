from flask import Flask, render_template
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
import flask_excel as excel

from flask import json
from datetime import datetime, date

from flask_login import current_user
from flask import jsonify
from functools import wraps

def permission(permission_id):
    """权限验证装饰器
    
    用于验证当前用户是否具有指定的权限。
    通过检查用户所属组织和角色的资源权限来判断。
    
    Args:
        permission_id: 需要验证的权限标识
        
    Returns:
        装饰器函数，用于包装需要进行权限验证的视图函数
    """
    def need_permission(func):
        @wraps(func)
        def inner(*args, **kargs):
            # 检查用户是否已登录
            if not current_user.ID:
                return jsonify(401, {"msg": "认证失败，无法访问系统资源"})
            else:
                resources = []
                resourceTree = []

                # 获取用户所属组织的资源权限
                resources += [res for org in current_user.organizations for res in org.resources if org.resources]
                # 获取用户所属角色的资源权限
                resources += [res for role in current_user.roles for res in role.resources if role.resources]
                
                # 去重处理
                new_dict = dict()
                for obj in resources:
                    if obj.ID not in new_dict:
                        new_dict[obj.ID] = obj

                # 构建权限树
                for resource in new_dict.values():
                    resourceTree.append(resource.PERMS)
                # 验证是否具有所需权限
                if permission_id in resourceTree:
                    return func(*args, **kargs)
                else:
                    return jsonify({'msg': '当前操作没有权限', 'code': 403})
        return inner
    return need_permission
        

JSONEncoder = json.JSONEncoder

class CustomJSONEncoder(JSONEncoder):
    """自定义JSON编码器
    
    继承自Flask的JSONEncoder，用于处理datetime和date类型的JSON序列化。
    将日期时间转换为指定格式的字符串。
    """
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return JSONEncoder.default(self, obj)

loginmanager = LoginManager()
loginmanager.session_protection = 'strong'
#loginmanager.login_view = 'base.login'

moment = Moment()
db = SQLAlchemy()


def create_app(config_name):
    """创建Flask应用实例
    
    初始化Flask应用，配置相关扩展，注册蓝图。
    
    Args:
        config_name: 配置名称，用于加载对应的配置对象
        
    Returns:
        配置完成的Flask应用实例
    """
    app = Flask(__name__)
    # 替换默认的json编码器
    app.json_encoder = CustomJSONEncoder
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化扩展
    moment.init_app(app)
    db.init_app(app)
    loginmanager.init_app(app)

    # 注册蓝图
    from .base import base as base_blueprint
    app.register_blueprint(base_blueprint)
    excel.init_excel(app)
    return app

