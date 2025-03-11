from datetime import datetime

from flask_login import current_user
from ..base import base
from ..models import Config
from flask import render_template, request, jsonify
from sqlalchemy import asc
from sqlalchemy import desc
from .. import  db
from flask_login import login_required
import flask_excel as excel
from .. import permission

# 根据配置键获取配置值
@base.route('/system/config/configKey/<configKey>', methods=['GET'])
@login_required
def sysconfig_get_value(configKey):
    """根据配置键获取配置值
    Args:
        configKey: 配置键名
    Returns:
        返回配置值，格式为JSON {code: 200, msg: 配置值}
    """
    data = Config.query.filter(Config.config_key == configKey).first()

    return jsonify({'code': 200, 'msg': data.config_value})


# 获取配置列表，支持分页和条件过滤
@base.route('/system/config/list', methods=['GET'])
@login_required
@permission('system:config:list')
def sys_config_list():
    """获取配置列表
    支持按配置名称、配置键名、配置类型过滤
    支持按创建时间范围过滤
    支持分页查询
    Returns:
        返回配置列表，格式为JSON {code: 200, msg: '操作成功', rows: [...], total: 总数}
    """
    # 构建过滤条件
    filters = []
    if 'configName' in request.args:
        filters.append(Config.config_name.like('%' + request.args['configName'] + '%'))
    if 'configKey' in request.args:
        filters.append(Config.config_key.like('%' + request.args['configKey'] + '%'))
    if 'configType' in request.args:
        filters.append(Config.config_type.like('%' + request.args['configType'] + '%'))

    # 按时间范围过滤
    if 'params[beginTime]' in request.args and 'params[endTime]' in request.args:
        filters.append(Config.create_time >  request.args['params[beginTime]'])
        filters.append(Config.create_time <  request.args['params[endTime]'])

    # 分页查询
    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    pagination = Config.query.filter(*filters).paginate(page=page, per_page=rows, error_out=False)
    config_list = pagination.items

    return jsonify({'msg': '操作成功', 'code': 200, 'rows': [config.to_json() for config in config_list], 'total': pagination.total})

# 根据ID获取配置详情
@base.route('/system/config/<id>', methods=['GET'])
@login_required
@permission('system:config:query')
def sysconfig_get_by_id(id):
    """根据ID获取配置详情
    Args:
        id: 配置ID
    Returns:
        返回配置详情，格式为JSON {code: 200, msg: '操作成功', data: {...}}
    """
    config = Config.query.get(id)

    return jsonify({'msg': '操作成功', 'code': 200, 'data': config.to_json()})

# 新增配置
@base.route('/system/config', methods=['POST'])
@login_required
@permission('system:config:add')
def sysconfig_add():
    """新增配置
    请求体参数:
        configKey: 配置键名
        configName: 配置名称
        configType: 配置类型
        configValue: 配置值
        remark: 备注
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    config = Config()

    if 'configKey' in request.json: config.config_key = request.json['configKey']
    if 'configName' in request.json: config.config_name = request.json['configName']
    if 'configType' in request.json: config.config_type = request.json['configType']
    if 'configValue' in request.json: config.config_value = request.json['configValue']
    if 'remark' in request.json: config.remark = request.json['remark']
    
    config.create_time = datetime.now()
    config.create_by = current_user.NAME

    db.session.add(config)

    return jsonify({'code': 200, 'msg': '操作成功'})

# 更新配置
@base.route('/system/config', methods=['PUT'])
@login_required
@permission('system:config:edit')
def sysconfig_update():
    """更新配置
    请求体参数:
        configId: 配置ID
        configKey: 配置键名
        configName: 配置名称
        configType: 配置类型
        configValue: 配置值
        remark: 备注
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    config = Config.query.get(request.json['configId'])

    if 'configKey' in request.json: config.config_key = request.json['configKey']
    if 'configName' in request.json: config.config_name = request.json['configName']
    if 'configType' in request.json: config.config_type = request.json['configType']
    if 'configValue' in request.json: config.config_value = request.json['configValue']
    if 'remark' in request.json: config.remark = request.json['remark']

    config.UPDATEDATETIME = datetime.now()
    config.update_by = current_user.NAME

    db.session.add(config)

    return jsonify({'msg': '操作成功', 'code': 200})

# 删除配置
@base.route('/system/config/<string:ids>', methods=['DELETE'])
@login_required
@permission('system:config:remove')
def syconfig_delete(ids):
    """删除配置
    Args:
        ids: 配置ID，多个ID用逗号分隔
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    idList = ids.split(',')
    for id in idList:
        config = Config.query.get(id)
        if config:
            db.session.delete(config)

    return jsonify({'code': 200, 'msg': '操作成功'})

# 导出配置
@base.route('/system/config/export', methods=['POST'])
@login_required
@permission('system:config:export')
def config_export():
    """导出配置列表为Excel文件
    Returns:
        返回Excel文件下载响应
    """
    rows = []
    rows.append(['参数主键', '参数名称', '参数键名', '参数键值', '系统内置', '备注', '创建时间'])

    configs = Config.query.all()
    for config in configs:
        row = []
        row.append(config.config_id)
        row.append(config.config_name)
        row.append(config.config_key)
        row.append(config.config_value)
        if config.config_type == 'Y':
            row.append('是')
        elif config.config_type == 'N':
            row.append('否')
        row.append(config.remark)
        row.append(config.create_time)

        rows.append(row)

    return excel.make_response_from_array(rows, "xlsx",
                                          file_name="config")
