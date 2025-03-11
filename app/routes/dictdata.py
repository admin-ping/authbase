# 导入所需的模块和依赖
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

@base.route('/system/dict/data/type/<dictType>', methods=['GET'])
@login_required
def sysdictdata_get_by_type(dictType):
    """根据字典类型查询字典数据
    
    Args:
        dictType: 字典类型
        
    Returns:
        返回指定类型的字典数据列表，格式为JSON {code: 200, msg: '操作成功', data: [...]}  
    """
    data_list = DictData.query.filter(DictData.dict_type == dictType)

    return jsonify({'msg': '操作成功', 'code': 200, 'data': [data.to_json() for data in data_list]})


@base.route('/system/dict/data/list', methods=['GET'])
@login_required
@permission('system:dict:list')
def sysdict_data_list():
    """获取字典数据列表
    
    支持按字典标签、字典类型和状态过滤
    支持分页查询
    
    Query Parameters:
        dictLabel: 字典标签，可选，支持模糊查询
        dictType: 字典类型，可选，支持模糊查询 
        status: 状态，可选，精确匹配
        pageNum: 页码，默认1
        pageSize: 每页记录数，默认10
        
    Returns:
        返回字典数据列表，格式为JSON {code: 200, msg: '操作成功', rows: [...], total: 总数}
    """
    filters = []
    if 'dictLabel' in request.args:
        filters.append(DictData.dict_label.like('%' + request.args['dictLabel'] + '%'))
    if 'dictType' in request.args:
        filters.append(DictData.dict_type.like('%' + request.args['dictType'] + '%'))

    if 'status' in request.args:
        filters.append(DictData.status == request.args['status'])

    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    pagination = DictData.query.filter(*filters).paginate(
        page=page, per_page=rows, error_out=False)
    data_list = pagination.items

    return jsonify({'msg': '操作成功', 'code': 200, 'rows': [data.to_json() for data in data_list], 'total': pagination.total})

@base.route('/system/dict/data/<id>', methods=['GET'])
@login_required
@permission('system:dict:query')
def sysdict_data_get_by_id(id):
    """根据ID查询字典数据
    
    Args:
        id: 字典数据ID
        
    Returns:
        返回字典数据详情，格式为JSON {code: 200, msg: '操作成功', data: {...}}
    """
    data = DictData.query.get(id)

    return jsonify({'msg': '操作成功', 'code': 200, 'data': data.to_json()})

@base.route('/system/dict/data', methods=['POST'])
@login_required
@permission('system:dict:add')
def sysdict_data_add():
    """新增字典数据
    
    请求体参数:
        dictLabel: 字典标签
        dictSort: 字典排序
        dictType: 字典类型
        dictValue: 字典键值
        listClass: 表格回显样式
        status: 状态
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    dictData = DictData()

    if 'dictLabel' in request.json: dictData.dict_label = request.json['dictLabel']
    if 'dictSort' in request.json: dictData.dict_sort = request.json['dictSort']
    if 'dictType' in request.json: dictData.dict_type = request.json['dictType']
    if 'dictValue' in request.json: dictData.dict_value = request.json['dictValue']
    if 'listClass' in request.json: dictData.list_class = request.json['listClass']
    if 'status' in request.json: dictData.status = request.json['status']

    dictData.create_time = datetime.now()
    dictData.create_by = current_user.NAME

    db.session.add(dictData)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/dict/data', methods=['PUT'])
@login_required
@permission('system:dict:edit')
def sysdict_data_update():
    """修改字典数据
    
    请求体参数:
        dictCode: 字典编码
        dictLabel: 字典标签
        dictSort: 字典排序
        dictType: 字典类型
        dictValue: 字典键值
        listClass: 表格回显样式
        status: 状态
        remark: 备注
        isDefault: 是否默认
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    dictData = DictData.query.get(request.json['dictCode'])

    if 'dictLabel' in request.json: dictData.dict_label = request.json['dictLabel']
    if 'dictSort' in request.json: dictData.dict_sort = request.json['dictSort']
    if 'dictType' in request.json: dictData.dict_type = request.json['dictType']
    if 'dictValue' in request.json: dictData.dict_value = request.json['dictValue']
    if 'listClass' in request.json: dictData.list_class = request.json['listClass']
    if 'status' in request.json: dictData.status = request.json['status']
    if 'remark' in request.json: dictData.remark = request.json['remark']
    if 'isDefault' in request.json: dictData.is_default = request.json['isDefault']

    dictData.update_time = datetime.now()
    dictData.update_by = current_user.NAME

    db.session.add(dictData)

    return jsonify({'msg': '操作成功', 'code': 200})

@base.route('/system/dict/data/<string:ids>', methods=['DELETE'])
@login_required
@permission('system:dict:remove')
def sydata_delete(ids):
    """删除字典数据
    
    Args:
        ids: 字典数据ID，多个ID用逗号分隔
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    idList = ids.split(',')
    for id in idList:
        dictData = DictData.query.get(id)
        if dictData:
            db.session.delete(dictData)

    return jsonify({'code': 200, 'msg': '操作成功'})


 
