from ..base import base
from ..models import Resource
from ..models import Role
from ..models import User
from ..models import Organization
from flask import g, jsonify, request
from flask_login import current_user, login_required
import json
from .. import db
from flask import render_template
from datetime import datetime
import uuid
from .. import permission

@base.route('/system/dept/list', methods=['GET'])
@login_required
@permission('system:dept:list')
def syorganization_treeGrid():
    """获取部门列表
    
    支持按部门名称过滤
    支持按部门状态过滤
    返回所有匹配的部门信息
    
    Query Parameters:
        deptName: 部门名称，可选，支持模糊查询
        status: 部门状态，可选，精确匹配
        
    Returns:
        返回部门列表，格式为JSON {msg: 提示信息, code: 状态码, data: [...部门列表]}
    """
    filters = []
    if 'deptName' in request.args:
        filters.append(Organization.NAME.like('%' + request.args['deptName'] + '%'))
    if 'status' in request.args:
        filters.append(Organization.STATUS == request.args['status'])

    orgs = Organization.query.filter(*filters)

    return jsonify({'msg': '操作成功', 'code': 200, "data": [org.to_json() for org in orgs]})

@base.route('/system/dept/treeselect', methods=['GET'])
@login_required
def syorganization_tree_select():
    """获取部门树形结构
    
    获取所有顶级部门及其子部门的树形结构
    用于前端部门选择组件展示
    
    Returns:
        返回部门树形结构，格式为JSON {msg: 提示信息, code: 状态码, data: [...部门树形数据]}
    """
    orgs = Organization.query.filter(Organization.SYORGANIZATION_ID == None)

    return jsonify({'msg': '操作成功', 'code': 200, "data": [org.to_tree_select_json() for org in orgs]}) 

@base.route('/system/dept/list/exclude/<id>', methods=['GET'])
@login_required
def syorganization_dept_list_exclude(id):
    """获取除指定ID外的部门列表
    
    获取系统中除了指定ID外的所有部门
    用于部门管理中选择上级部门时过滤自身
    
    Args:
        id: 要排除的部门ID
        
    Returns:
        返回部门列表，格式为JSON {msg: 提示信息, code: 状态码, data: [...部门列表]}
    """
    orgs = Organization.query.filter(Organization.ID != id)

    return jsonify({'msg': '操作成功', 'code': 200, "data": [org.to_json() for org in orgs]})

@base.route('/system/dept/<string:id>', methods=['GET'])
@login_required
@permission('system:dept:query')
def syorganization_getById(id):
    """根据ID获取部门信息
    
    获取指定ID的部门详细信息
    
    Args:
        id: 部门ID
        
    Returns:
        成功返回部门信息 {msg: 提示信息, code: 200, data: 部门信息}
        失败返回错误信息 {success: false, msg: 错误信息}
    """
    org = Organization.query.get(id)

    if org:
        return jsonify({'msg': '操作成功', 'code': 200, 'data': org.to_json()})
    else:
        return jsonify({'success': False, 'msg': 'error'})

@base.route('/system/dept', methods=['PUT'])
@login_required
@permission('system:dept:edit')
def syorganization_update():
    """更新部门信息
    
    更新部门的基本信息，包括名称、邮箱、负责人、电话等
    
    Json Parameters:
        deptId: 部门ID
        deptName: 部门名称，可选
        email: 邮箱，可选
        leader: 负责人，可选
        phone: 电话，可选
        orderNum: 显示顺序，可选
        parentId: 上级部门ID，可选
        status: 部门状态，可选
        
    Returns:
        返回操作结果 {code: 状态码, msg: 提示信息}
    """
    org = Organization.query.get(request.json['deptId'])

    org.UPDATEDATETIME = datetime.now()
    if 'deptName' in request.json:  org.NAME = request.json['deptName']
    if 'email' in request.json: org.EMAIL = request.json['email']
    if 'leader' in request.json: org.LEADER = request.json['leader']
    if 'phone' in request.json: org.PHONE = request.json['phone']
    if 'orderNum' in request.json:  org.SEQ = request.json['orderNum']
    if 'parentId' in request.json: org.parent = Organization.query.get(request.json['parentId'])
    if 'status' in request.json: org.STATUS = request.json['status']

    db.session.add(org)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/dept', methods=['POST'])
@login_required
@permission('system:dept:add')
def syorganization_save():
    """新增部门
    
    创建新的部门，并关联到当前用户
    
    Json Parameters:
        deptName: 部门名称，可选
        email: 邮箱，可选
        leader: 负责人，可选
        phone: 电话，可选
        orderNum: 显示顺序，可选
        parentId: 上级部门ID，可选
        status: 部门状态，可选
        
    Returns:
        返回操作结果 {code: 状态码, msg: 提示信息}
    """
    org = Organization()
    org.ID = str(uuid.uuid4())
    if 'deptName' in request.json:  org.NAME = request.json['deptName']
    if 'email' in request.json: org.EMAIL = request.json['email']
    if 'leader' in request.json: org.LEADER = request.json['leader']
    if 'phone' in request.json: org.PHONE = request.json['phone']
    if 'orderNum' in request.json: org.SEQ = request.json['orderNum']
    if 'parentId' in request.json: org.parent = Organization.query.get(request.json['parentId'])
    if 'status' in request.json: org.STATUS = request.json['status']

    # 将新部门添加到当前用户的组织列表中
    current_user.organizations.append(org)

    db.session.add(org)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/dept/<string:id>', methods=['DELETE'])
@login_required
@permission('system:dept:remove')
def sydept_delete(id):
    """删除部门
    
    删除指定ID的部门
    
    Args:
        id: 要删除的部门ID
        
    Returns:
        返回操作结果 {code: 状态码, msg: 提示信息}
    """
    org = Organization.query.get(id)
    if org:
        db.session.delete(org)

    return jsonify({'code': 200, 'msg': '操作成功'})
