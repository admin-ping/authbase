# coding:utf-8
from ..base import base
from ..models import Resource, Organization
from ..models import Role
from ..models import User
from flask import g, jsonify
from flask_login import current_user
import json
from ..models import ResourceType
from flask import render_template, request
from .. import  db
import uuid
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy import asc
from flask_login import login_required  
from .. import permission

@base.route('/system/menu/list', methods=['GET'])
@login_required
@permission('system:menu:list')
def syresource_treeGrid():
    """获取菜单列表
    
    支持按菜单名称过滤
    按照菜单ID和排序号排序
    返回所有匹配的菜单信息
    
    Query Parameters:
        menuName: 菜单名称，可选，支持模糊查询
        
    Returns:
        返回菜单列表，格式为JSON {msg: 提示信息, code: 状态码, data: [...菜单列表]}
    """
    filters = []
    if 'menuName' in request.args:
        filters.append(Resource.NAME.like('%' + request.args['menuName'] + '%'))

    order_by = []
    order_by.append(asc(getattr(Resource, 'SYRESOURCE_ID')))
    order_by.append(asc(getattr(Resource, 'SEQ')))

    res_list = Resource.query.filter(*filters).order_by(*order_by)

    return jsonify({"msg":"操作成功","code":200, "data": [org.to_json() for org in res_list]})

@base.route('/system/menu/<id>', methods=['GET'])
@login_required
@permission('system:menu:query')
def syresource_getById(id):
    """根据ID获取菜单信息
    
    获取指定ID的菜单详细信息
    
    Args:
        id: 菜单ID
        
    Returns:
        成功返回菜单信息 {code: 200, msg: 操作成功, data: 菜单信息}
        失败返回错误信息 {success: false, msg: error}
    """
    res = Resource.query.get(id)

    if res:
        return jsonify({'code': 200, 'msg': '操作成功', 'data': res.to_json()})
    else:
        return jsonify({'success': False, 'msg': 'error'})

@base.route('/system/menu', methods=['PUT'])
@login_required
@permission('system:menu:edit')
def syresource_update():
    """更新菜单信息
    
    更新菜单的基本信息，包括图标、组件、路径、名称等
    
    Json Parameters:
        menuId: 菜单ID
        icon: 菜单图标，可选
        component: 组件路径，可选
        path: 路由地址，可选
        menuName: 菜单名称，可选
        orderNum: 显示顺序，可选
        perms: 权限标识，可选
        menuType: 菜单类型(M目录 C菜单 F按钮)，可选
        parentId: 父菜单ID，可选
        status: 菜单状态，可选
        
    Returns:
        返回操作结果 {code: 200, msg: 操作成功}
    """
    res = Resource.query.get(request.json['menuId'])

    res.UPDATEDATETIME = datetime.now()
    if 'icon' in request.json: res.ICONCLS = request.json['icon']
    if 'component' in request.json: res.URL = request.json['component']
    if 'path' in request.json: res.PATH = request.json['path']
    if 'menuName' in request.json: res.NAME = request.json['menuName']
    if 'orderNum' in request.json: res.SEQ = request.json['orderNum']
    if 'perms' in request.json: res.PERMS = request.json['perms']
    if 'menuType' in request.json: res.SYRESOURCETYPE_ID = '1' if request.json['menuType'] == 'F' else '0' if request.json['menuType'] == 'C' else '3'
    if 'parentId' in request.json: res.parent = Resource.query.get(request.json['parentId'])
    if 'status' in request.json: res.STATUS = request.json['status']

    db.session.add(res)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/menu', methods=['POST'])
@login_required
@permission('system:menu:add')
def syresource_save():
    """新增菜单
    
    创建新的菜单资源
    
    Json Parameters:
        icon: 菜单图标，可选
        component: 组件路径，可选
        path: 路由地址，可选
        menuName: 菜单名称，可选
        orderNum: 显示顺序，可选
        perms: 权限标识，可选
        menuType: 菜单类型(M目录 C菜单 F按钮)，可选
        parentId: 父菜单ID，可选
        status: 菜单状态，可选
        
    Returns:
        返回操作结果 {code: 200, msg: 操作成功}
    """
    res = Resource()

    res.ID = str(uuid.uuid4())
    if 'icon' in request.json: res.ICONCLS = request.json['icon']
    if 'component' in request.json: res.URL = request.json['component']
    if 'path' in request.json: res.PATH = request.json['path']
    if 'menuName' in request.json: res.NAME = request.json['menuName']
    if 'orderNum' in request.json: res.SEQ = request.json['orderNum']
    if 'perms' in request.json: res.PERMS = request.json['perms']
    if 'menuType' in request.json: res.SYRESOURCETYPE_ID = '1' if request.json['menuType'] == 'F' else '0' if request.json['menuType'] == 'F' else '3'
    if 'parentId' in request.json:
        parent = Resource.query.filter(Resource.ID == request.json['parentId']).first()
        res.parent = parent
    if 'status' in request.json: res.STATUS = request.json['status']

    db.session.add(res)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/menu/<id>', methods=['DELETE'])
@login_required
@permission('system:menu:remove')
def syresource_delete(id):
    """删除菜单
    
    删除指定ID的菜单
    
    Args:
        id: 要删除的菜单ID
        
    Returns:
        返回操作结果 {code: 200, msg: 操作成功}
    """
    res = Resource.query.get(id)
    if res:
        db.session.delete(res)

    return jsonify({'code': 200, 'msg': '操作成功'})

@base.route('/system/menu/treeselect', methods=['GET'])
@login_required
def syresource_tree_select():
    """获取菜单树形结构
    
    获取所有顶级菜单及其子菜单的树形结构
    用于前端菜单选择组件展示
    
    Returns:
        返回菜单树形结构，格式为JSON {msg: 操作成功, code: 200, data: [...菜单树形数据]}
    """
    resList = Resource.query.filter(Resource.SYRESOURCE_ID == None)

    return jsonify({'msg': '操作成功', 'code': 200, "data": [res.to_tree_select_json() for res in resList]})

@base.route('/system/menu/roleMenuTreeselect/<roleId>', methods=['GET'])
@login_required
def syresource_role_tree_select(roleId):
    """获取角色菜单树形结构
    
    获取指定角色的菜单树形结构，包含已分配菜单的选中状态
    
    Args:
        roleId: 角色ID
        
    Returns:
        返回角色菜单树形结构，格式为JSON:
        {msg: 操作成功, code: 200, 
         menus: [...菜单树形数据],
         checkedKeys: [...已分配菜单ID列表]}
    """
    role = Role.query.get(roleId)
    resList = Resource.query.filter(Resource.SYRESOURCE_ID == None)

    return jsonify({'msg': '操作成功', 'code': 200, \
        "menus": [res.to_tree_select_json() for res in resList], \
        "checkedKeys": [res.ID for res in role.resources]})

