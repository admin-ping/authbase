# coding:utf-8
from app.models.Organization import Organization
from ..base import base
from ..models import Role, Resource, User
from flask import render_template, request
from flask_login import current_user
from flask import jsonify
from datetime import datetime
from .. import  db
import uuid
from sqlalchemy import desc
from sqlalchemy import asc
from sqlalchemy import or_
from flask_login import login_required
from .. import permission


@base.route('/system/role/authUser/cancelAll', methods=['PUT'])
@login_required
def cancel_all_role():
    """批量取消用户角色关联
    
    取消多个用户与指定角色的关联关系
    
    Query Parameters:
        roleId: 角色ID
        userIds: 用户ID列表，多个ID用逗号分隔
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '取消成功'}
    """
    roleId = request.args.get('roleId')
    userIds = request.args.get('userIds')

    #role = Role.query.get(roleId)
    idList = userIds.split(',')
    #toCancelUsers = [User.query.get(uid) for uid in idList]
    #role.users = [user2  for user2 in role.users.all() for user in toCancelUsers if user2.ID != user.ID ]
    for userId in idList:
        user = User.query.get(userId)
        user.roles = [role for role in user.roles.all() if role.ID != roleId]
        db.session.add(user)

    return jsonify({'code': 200, 'msg': '取消成功'})

@base.route('/system/role/authUser/cancel', methods=['PUT'])
@login_required
def cancel_role():
    """取消单个用户角色关联
    
    取消单个用户与指定角色的关联关系
    
    Json Parameters:
        roleId: 角色ID
        userId: 用户ID
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '取消成功'}
    """
    roleId = request.json.get('roleId')
    userId = request.json.get('userId')

    user = User.query.get(userId)
    user.roles = [role for role in user.roles.all() if role.ID != roleId]
    db.session.add(user)

    return jsonify({'code': 200, 'msg': '取消成功'})

@base.route('/system/role/list', methods=['GET'])
@login_required
@permission('system:role:list')
def grid():
    """获取角色列表
    
    支持按角色名称过滤
    支持分页查询
    
    Query Parameters:
        roleName: 角色名称，可选，支持模糊查询
        pageNum: 页码，默认1
        pageSize: 每页记录数，默认10
        
    Returns:
        返回角色列表，格式为JSON {rows: [...角色列表], total: 总数}
    """
    filters = []
    if request.args.get('roleName'):
        filters.append(Role.NAME.like('%' + request.args.get('roleName') + '%'))
    if request.args.get('status'):
        filters.append(Role.STATUS == request.args.get('status'))

    order_by = []
    if request.form.get('sort'):
        if request.form.get('order') == 'asc':
            order_by.append(asc(getattr(Role,request.form.get('sort').upper())))
        elif request.form.get('order') == 'desc':
            order_by.append(desc(getattr(Role,request.form.get('sort').upper())))
        else:
            order_by.append(getattr(Role,request.form.get('sort').upper()))

    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    pagination = current_user.roles.filter(*filters).order_by(*order_by).paginate(
        page=page, per_page=rows, error_out=False)
    roles = pagination.items

    return jsonify({'rows': [role.to_json() for role in roles], 'total': pagination.total})

@base.route('/system/role/<string:id>', methods=['GET'])
@login_required
@permission('system:role:query')
def syrole_getById(id):
    """根据ID查询角色信息
    
    Args:
        id: 角色ID
        
    Returns:
        成功返回角色信息 {code: 200, msg: '操作成功', data: 角色信息}
        失败返回错误信息 {success: false, msg: 'error'}
    """
    role = Role.query.get(id)

    if role:
        return jsonify({'code': 200, 'msg': '操作成功', 'data': role.to_json()})
    else:
        return jsonify({'success': False, 'msg': 'error'})

@base.route('/system/role', methods=['PUT'])
@login_required
@permission('system:role:edit')
def syrole_update():
    """更新角色信息
    
    更新角色的基本信息，包括名称、备注、排序号等
    支持更新角色的菜单权限
    
    Json Parameters:
        roleId: 角色ID
        roleName: 角色名称
        remark: 备注
        roleSort: 显示顺序
        roleKey: 权限字符，可选
        dataScope: 数据范围，可选
        menuIds: 菜单ID列表，可选
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    role = Role.query.get(request.json['roleId'])

    role.UPDATEDATETIME = datetime.now()
    role.NAME = request.json['roleName']
    role.DESCRIPTION = request.json['remark']
    role.SEQ = request.json['roleSort']
    if 'roleKey' in request.json: role.ROLEKEY = request.json['roleKey']
    if 'dataScope' in request.json: role.DATASCOPE = request.json['dataScope']

    if 'menuIds' in request.json:
        res_list = [Resource.query.get(menuId) for menuId in request.json['menuIds']]
        role.resources = res_list

    db.session.add(role)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/role', methods=['POST'])
@login_required
@permission('system:role:add')
def syrole_save():
    """新增角色
    
    创建新的角色，并关联到当前用户
    支持设置角色的菜单权限
    
    Json Parameters:
        roleName: 角色名称
        roleKey: 权限字符，可选
        remark: 备注，可选
        roleSort: 显示顺序
        dataScope: 数据范围，可选
        menuIds: 菜单ID列表，可选
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    role = Role()

    role.ID = str(uuid.uuid4())
    role.NAME = request.json['roleName']
    if 'roleKey' in request.json: role.ROLEKEY = request.json['roleKey']
    if 'remark' in request.json: role.DESCRIPTION = request.json['remark']
    role.SEQ = request.json['roleSort']
    if 'dataScope' in request.json: role.DATASCOPE = request.json['dataScope']

    if 'menuIds' in request.json:
        res_list = [Resource.query.get(menuId) for menuId in request.json['menuIds']]
        role.resources = res_list
        
    # 将新角色添加到当前用户的角色列表中
    current_user.roles.append(role)

    db.session.add(role)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/role/<string:id>', methods=['DELETE'])
@login_required
@permission('system:role:remove')
def syrole_delete(id):
    """删除角色
    
    删除指定ID的角色
    
    Args:
        id: 要删除的角色ID
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    role = Role.query.get(id)
    if role:
        db.session.delete(role)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/role/authUser/allocatedList', methods=['GET'])
@login_required
def allocatedList():
    """获取已分配用户角色列表
    
    获取已分配指定角色的用户列表
    支持分页查询
    
    Query Parameters:
        roleId: 角色ID
        pageNum: 页码，默认1
        pageSize: 每页记录数，默认10
        
    Returns:
        返回用户列表，格式为JSON {rows: [...用户列表], total: 总数}
    """
    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    pagination = User.query.join(Role, User.roles).filter(Role.ID == request.args['roleId']).paginate(
        page=page, per_page=rows, error_out=False)
    users = pagination.items

    return jsonify({'rows': [user.to_json() for user in users], 'total': pagination.total})

@base.route('/system/role/authUser/unallocatedList', methods=['GET'])
@login_required
def unallocatedList():
    """获取未分配用户角色列表
    
    获取未分配指定角色的用户列表
    支持分页查询
    
    Query Parameters:
        roleId: 角色ID
        pageNum: 页码，默认1
        pageSize: 每页记录数，默认10
        
    Returns:
        返回用户列表，格式为JSON {rows: [...用户列表], total: 总数}
    """
    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageNum', 10, type=int)
    pagination = User.query.join(Role, User.roles).filter(or_(Role.ID != request.args['roleId'], Role.ID == None)).paginate(
        page=page, per_page=rows, error_out=False)
    users = pagination.items

    return jsonify({'rows': [user.to_json() for user in users], 'total': pagination.total})


@base.route('/system/dept/roleDeptTreeselect/<id>', methods=['GET'])
@login_required
def roleDeptTreeselect(id):
    """获取角色部门树结构
    
    获取指定角色的部门树形结构，包含已分配部门的选中状态
    
    Args:
        id: 角色ID
        
    Returns:
        返回部门树形结构，格式为JSON:
        {code: 200, msg: '操作成功', 
         checkedKeys: [...已分配部门ID列表],
         depts: [...部门树形数据]}
    """
    role = Role.query.get(id)
    dept = Organization.query.get('0')

    return jsonify({'code': 200, 'msg': '操作成功', 'checkedKeys': [dept.ID for dept in role.depts], \
         'depts': [dept.to_tree_select_json()]})

@base.route('/system/role/dataScope', methods=['PUT'])
@login_required
def syrole_dataScope():
    """修改角色数据权限
    
    更新角色的数据范围和关联部门
    
    Json Parameters:
        roleId: 角色ID
        dataScope: 数据范围，可选
        deptIds: 部门ID列表，可选
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    role = Role.query.get(request.json['roleId'])

    if 'dataScope' in request.json: role.DATASCOPE = request.json['dataScope']
    if 'deptIds' in request.json:
        dept_list = [Organization.query.get(deptId) for deptId in request.json['deptIds']]
        role.depts = dept_list
    
    db.session.add(role)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/role/authUser/selectAll', methods=['PUT'])
@login_required
def syrole_authUser_selectAll():
    """批量选择用户添加到角色
    
    批量添加用户与指定角色的关联关系
    
    Query Parameters:
        roleId: 角色ID
        userIds: 用户ID列表，多个ID用逗号分隔
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    role = Role.query.get(request.args.get('roleId'))
    userIds = request.args.get('userIds')

    idList = userIds.split(',')
    for userId in idList:
        user = User.query.get(userId)
        user.roles.append(role)
        db.session.add(user)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/role/changeStatus', methods=['PUT'])
@login_required
@permission('system:role:edit')
def syrole_status_update():
    """更新角色状态
    
    更新角色的启用/禁用状态
    
    Json Parameters:
        roleId: 角色ID
        status: 状态值
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    role = Role.query.get(request.json['roleId'])

    if 'status' in request.json: role.STATUS = request.json['status']

    db.session.add(role)

    return jsonify({'code': 200, 'msg': '操作成功'})
