from datetime import datetime

from flask_login import current_user
from ..base import base
from ..models import DictData, DictType
from flask import render_template, request, jsonify
from sqlalchemy import asc
from sqlalchemy import desc
from .. import  db
from flask_login import login_required
from .. import permission

@base.route('/system/dict/type/list', methods=['GET'])
@login_required
@permission('system:dict:list')
def sysdict_type_list():
    """获取字典类型列表
    
    支持按字典名称、字典类型和状态过滤
    支持按创建时间范围过滤
    支持分页查询
    
    Query Parameters:
        dictName: 字典名称，可选，支持模糊查询
        dictType: 字典类型，可选，支持模糊查询
        status: 状态，可选，精确匹配
        params[beginTime]: 开始时间，可选
        params[endTime]: 结束时间，可选
        pageNum: 页码，默认1
        pageSize: 每页记录数，默认10
        
    Returns:
        返回字典类型列表，格式为JSON {code: 200, msg: '操作成功', rows: [...], total: 总数}
    """
    filters = []
    if 'dictName' in request.args:
        filters.append(DictType.dict_name.like('%' + request.args['dictName'] + '%'))
    if 'dictType' in request.args:
        filters.append(DictType.dict_type.like('%' + request.args['dictType'] + '%'))

    if 'status' in request.args:
        filters.append(DictType.status == request.args['status'])


    if 'params[beginTime]' in request.args and 'params[endTime]' in request.args:
        filters.append(DictType.create_time >  request.args['params[beginTime]'])
        filters.append(DictType.create_time <  request.args['params[endTime]'])

    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    pagination = DictType.query.filter(*filters).paginate(
        page=page, per_page=rows, error_out=False)
    types = pagination.items

    return jsonify({'msg': '操作成功', 'code': 200, 'rows': [type.to_json() for type in types], 'total': pagination.total})

@base.route('/system/dict/type/<id>', methods=['GET'])
@login_required
@permission('system:dict:query')
def sysdict_type_get_by_id(id):
    """根据ID查询字典类型
    
    Args:
        id: 字典类型ID
        
    Returns:
        返回字典类型详情，格式为JSON {code: 200, msg: '操作成功', data: {...}}
    """
    type = DictType.query.get(id)

    return jsonify({'msg': '操作成功', 'code': 200, 'data': type.to_json()})

@base.route('/system/dict/type', methods=['POST'])
@login_required
@permission('system:dict:add')
def sysdict_type_add():
    """新增字典类型
    
    请求体参数:
        dictName: 字典名称
        dictType: 字典类型
        status: 状态
        remark: 备注
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    dictType = DictType()

    if 'dictName' in request.json: dictType.dict_name = request.json['dictName']
    if 'status' in request.json: dictType.status = request.json['status']
    if 'remark' in request.json: dictType.remark = request.json['remark']
    if 'dictType' in request.json: dictType.dict_type = request.json['dictType']

    dictType.create_time = datetime.now()
    dictType.create_by = current_user.NAME
    dictType.update_time = datetime.now()
    dictType.update_by = current_user.NAME

    db.session.add(dictType)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/dict/type', methods=['PUT'])
@login_required
@permission('system:dict:edit')
def sysdict_type_update():
    """修改字典类型
    
    请求体参数:
        dictId: 字典类型ID
        dictName: 字典名称
        dictType: 字典类型
        status: 状态
        remark: 备注
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    dictType = DictType.query.get(request.json['dictId'])

    if 'dictName' in request.json: dictType.dict_name = request.json['dictName']
    if 'status' in request.json: dictType.status = request.json['status']
    if 'remark' in request.json: dictType.remark = request.json['remark']
    if 'dictType' in request.json: dictType.dict_type = request.json['dictType']

    dictType.update_time = datetime.now()
    dictType.update_by = current_user.NAME

    db.session.add(dictType)

    return jsonify({'msg': '操作成功', 'code': 200})

@base.route('/system/dict/type/<string:ids>', methods=['DELETE'])
@login_required
@permission('system:dict:remove')
def sytype_delete(ids):
    """删除字典类型
    
    Args:
        ids: 字典类型ID，多个ID用逗号分隔
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    idList = ids.split(',')
    for id in idList:
        dictType = DictType.query.get(id)
        if dictType:
            db.session.delete(dictType)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/dict/type/optionselect', methods=['GET'])
@login_required
def sysdict_type_all():
    """获取所有字典类型选项
    
    Returns:
        返回所有字典类型列表，格式为JSON {code: 200, msg: '操作成功', data: [...]}
    """
    types = DictData.query.all()

    return jsonify({'msg': '操作成功', 'code': 200, 'data': [type.to_json() for type in types]})   

