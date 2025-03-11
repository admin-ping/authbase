# coding:utf-8

# 导入所需的模块和依赖
from ..base import base
from ..models import User, Organization, Role, OnLine
from flask import render_template, request
from flask import g, jsonify
import hashlib
from flask_login import login_user, logout_user, login_required, \
    current_user
from datetime import datetime
from .. import  db
import uuid
from sqlalchemy import asc, true
from sqlalchemy import desc
from sqlalchemy import text
import flask_excel as excel
from .. import permission

@base.route('/system/user/authRole', methods=['PUT'])
@login_required
@permission('system:role:edit')
def grant_user_role():
    """分配用户角色
    
    为指定用户分配角色权限
    
    Query Parameters:
        userId: 用户ID
        roleIds: 角色ID列表，多个ID用逗号分隔
        
    Returns:
        返回操作结果，格式为JSON {code: 200, msg: '操作成功'}
    """
    id = request.args['userId']
    ids = request.args['roleIds']

    user = User.query.get(id)

    if not ids:
        user.roles = []
    else:
        idList = ids.split(',')
        user.roles = [Role.query.get(rid) for rid in idList]

    db.session.add(user)

    return jsonify({'code': 200, 'msg': '操作成功'})

@login_required
def record_login_history(type):
    """记录用户登录历史
    
    记录用户的登录/登出操作
    
    Args:
        type: 操作类型，1表示登录，0表示登出
    """
    online = OnLine()
    online.ID = str(uuid.uuid4())
    online.LOGINNAME = current_user.LOGINNAME
    online.IP = request.remote_addr
    online.TYPE = type
    db.session.add(online)

@base.route('/logout', methods=['POST'])
@login_required
def do_logout():
    """用户登出
    
    处理用户登出请求，记录登出历史
    
    Returns:
        返回登出结果，格式为JSON {success: true}
    """
    record_login_history(0)
    logout_user()
    return jsonify({'success': True})

@base.route('/login', methods=['POST'])
def do_login():
    """用户登录
    
    处理用户登录请求，验证用户名密码
    
    Json Parameters:
        username: 用户名
        password: 密码
        
    Returns:
        登录成功返回 {msg: '登录成功~', code: 200, url: '/', token: uuid}
        登录失败返回 {msg: '登录失败,账号密码错误~', code: 500}
    """
    #检查用户名是否存在
    user = User.query.filter_by(LOGINNAME=request.json['username']).first()
    
    if user is not None:
        md = hashlib.md5()
        #提交的密码MD5加密
        md.update(request.json['password'].encode('utf-8'))
        #MD5加密后的内容同数据库密码比较
        if md.hexdigest() == user.PWD:
            login_user(user)
            record_login_history(1)
            return jsonify({'msg': '登录成功~', 'code': 200, 'url': '/', 'token': str(uuid.uuid4())})
    return jsonify({'msg': '登录失败,账号密码错误~', 'code': 500})

@base.route('/system/user/list', methods=['GET'])
@login_required
@permission('system:user:list')
def user_grid():
    """获取用户列表
    
    支持按用户名、手机号码过滤
    支持按创建时间范围过滤
    支持按部门ID过滤
    支持分页查询
    
    Query Parameters:
        userName: 用户名，可选，支持模糊查询
        phonenumber: 手机号码，可选，支持模糊查询
        params[beginTime]: 开始时间，可选
        params[endTime]: 结束时间，可选
        deptId: 部门ID，可选
        pageNum: 页码，默认1
        pageSize: 每页记录数，默认10
        
    Returns:
        返回用户列表，格式为JSON {rows: [...用户列表], total: 总数, code: 200, msg: '查询成功'}
    """
    filters = []
    if 'userName' in request.args:
        filters.append(User.LOGINNAME.like('%' + request.args['userName'] + '%'))
    if 'phonenumber' in request.args:
        filters.append(User.PHONENUMBER.like('%' + request.args['phonenumber'] + '%'))
    if 'params[beginTime]' in request.args and 'params[endTime]' in request.args:
        filters.append(User.CREATEDATETIME >  request.args['params[beginTime]'])
        filters.append(User.CREATEDATETIME <  request.args['params[endTime]'])

    order_by = []
    if request.form.get('sort'):
        if request.form.get('order') == 'asc':
            order_by.append(asc(getattr(User,request.form.get('sort').upper())))
        elif request.form.get('order') == 'desc':
            order_by.append(desc(getattr(User,request.form.get('sort').upper())))
        else:
            order_by.append(getattr(User,request.form.get('sort').upper()))

    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    if 'deptId' in request.args:
        # Define a recursive CTE
        dept_cte = (
            db.session.query(Organization.ID)
            .filter(Organization.ID == request.args['deptId'])
            .cte('dept_tree', recursive=True)
        )
        
        # Recursive part of the CTE
        dept_cte = dept_cte.union_all(
            db.session.query(Organization.ID)
            .join(dept_cte, Organization.SYORGANIZATION_ID == dept_cte.c.ID)
        )
        pagination = User.query.join(Organization, User.organizations).join(
            dept_cte, Organization.ID == dept_cte.c.ID).filter(*filters).params(
            dept_id=request.args['deptId']).order_by(*order_by).paginate(
            page=page, per_page=rows, error_out=False)
    else:
        pagination = User.query.filter(*filters).order_by(*order_by).paginate(
            page=page, per_page=rows, error_out=False)
    users = pagination.items

    return jsonify({'rows': [user.to_json() for user in users], 'total': pagination.total, 'code': 200, 'msg': '查询成功'})

@base.route('/system/user/', methods=['GET'])
@login_required
def syuser_get():
    """获取用户基础信息
    
    获取所有角色列表和岗位列表
    
    Returns:
        返回角色和岗位信息，格式为JSON {code: 200, msg: '', roles: [...角色列表], posts: []}
    """
    json = {'code': 200, 'msg': ''}
    json['roles'] = [role.to_json() for role in Role.query.all()]
    json['posts'] = []
    return jsonify(json)

@base.route('/system/user/<id>', methods=['GET'])
@login_required
@permission('system:user:query')
def syuser_getById(id):
    """根据ID获取用户信息
    
    获取指定用户的详细信息，包括角色信息
    
    Args:
        id: 用户ID
        
    Returns:
        成功返回用户信息 {code: 200, msg: '', data: 用户信息, roles: [...用户角色], roleIds: [...角色ID]}
        失败返回错误信息 {success: false, msg: 'error'}
    """
    user = User.query.get(id)

    if user:
        json = {'code': 200, 'msg': '', 'data': user.to_json()}
        if len(user.roles.all()) > 0:
            json['roles'] = [role.to_json() for role in user.roles]
            json['roleIds'] = [role.ID for role in user.roles]

        return jsonify(json)
    else:
        return jsonify({'success': False, 'msg': 'error'})

@base.route('/system/user', methods=['PUT'])
@login_required
@permission('system:user:edit')
def syuser_update():
    """更新用户信息
    
    更新用户的基本信息，包括昵称、性别、邮箱、电话等
    支持更新用户的部门和角色
    
    Json Parameters:
        userId: 用户ID
        userName: 用户名
        nickName: 昵称，可选
        sex: 性别，可选
        email: 邮箱，可选
        phonenumber: 电话，可选
        deptId: 部门ID，可选
        roleIds: 角色ID列表，可选
        
    Returns:
        返回操作结果 {code: 200, msg: '更新成功！'}
    """
    id = request.json['userId']
    userName = request.json['userName']
    
    # if User.query.filter(User.LOGINNAME == loginname).filter(User.ID != id).first():
    #     return jsonify({'code': 201, 'msg': '更新用户失败，用户名已存在！'})

    user = User.query.get(id)

    user.UPDATEDATETIME = datetime.now()
    if 'nickName' in request.json: user.NAME = request.json['nickName'] 
    if 'sex' in request.json: user.SEX = request.json['sex']
    if 'email' in request.json: user.EMAIL = request.json['email']
    if 'phonenumber' in request.json: user.PHONENUMBER = request.json['phonenumber']
    if 'deptId' in request.json: user.organizations = Organization.query.filter(Organization.ID == request.json['deptId']).all()
    if 'roleIds' in request.json:
        user.roles = [Role.query.get(roleId) for roleId in request.json['roleIds']]

    db.session.add(user)

    return jsonify({'code': 200, 'msg': '更新成功！'})

@base.route('/system/user', methods=['POST'])
@login_required
@permission('system:user:add')
def syuser_save():
    """新增用户
    
    创建新的用户，设置基本信息和关联信息
    
    Json Parameters:
        userName: 用户名
        password: 密码
        nickName: 昵称，可选
        sex: 性别，可选
        email: 邮箱，可选
        phonenumber: 电话，可选
        deptId: 部门ID，可选
        roleIds: 角色ID列表，可选
        
    Returns:
        成功返回 {code: 200, msg: '新建用户成功！'}
        失败返回 {success: false, msg: '新建用户失败，用户名已存在！'}
    """
    if User.query.filter_by(LOGINNAME = request.json['userName']).first():
        return jsonify({'success': False, 'msg': '新建用户失败，用户名已存在！'})

    user = User()

    user.ID = str(uuid.uuid4())

    md = hashlib.md5()
    md.update(request.json['password'].encode('utf-8'))
    user.PWD = md.hexdigest()

    with db.session.no_autoflush:
        if 'nickName' in request.json: user.NAME = request.json['nickName'] 
        if 'sex' in request.json: user.SEX = request.json['sex']
        if 'email' in request.json: user.EMAIL = request.json['email']
        if 'phonenumber' in request.json: user.PHONENUMBER = request.json['phonenumber']
        if 'deptId' in request.json: user.organizations = Organization.query.filter(Organization.ID == request.json['deptId']).all()
        if 'roleIds' in request.json:
            user.roles = [Role.query.get(roleId) for roleId in request.json['roleIds']]

        user.LOGINNAME = request.json['userName']

        # add current use to new user
        #current_user.roles.append(user)

        db.session.add(user)

    return jsonify({'code': 200, 'msg': '新建用户成功！'})

@base.route('/system/user/<id>', methods=['DELETE'])
@login_required
@permission('system:user:remove')
def syuser_delete(id):
    """删除用户
    
    删除指定ID的用户
    
    Args:
        id: 要删除的用户ID
        
    Returns:
        返回操作结果 {code: 200, msg: '删除成功'}
    """
    user = User.query.get(id)
    if user:
        db.session.delete(user)

    return jsonify({'code': 200, 'msg': '删除成功'})

@base.route('/system/user/profile/updatePwd', methods=['PUT']) 
@login_required
def syuser_update_pwd():
    """修改用户密码
    
    修改当前登录用户的密码
    
    Query Parameters:
        oldPassword: 旧密码
        newPassword: 新密码
        
    Returns:
        成功返回 {code: 200, msg: '修改成功'}
        失败返回 {code: 400, msg: '旧密码错误'}
    """
    user = User.query.get(current_user.ID)

    if user:
        md = hashlib.md5()
        #提交的密码MD5加密
        md.update(request.args.get('oldPassword').encode('utf-8'))
        #MD5加密后的内容同数据库密码比较
        if md.hexdigest() != user.PWD:
            return jsonify({'code': 400, 'msg': '旧密码错误'})

        md = hashlib.md5()
        md.update(request.args.get('newPassword').encode('utf-8'))
        user.PWD = md.hexdigest()
        db.session.add(user)
    return jsonify({'code': 200, 'msg': '修改成功'})

@base.route('/getInfo', methods=['GET'])
@login_required
def syuser_info():
    """获取当前用户信息
    
    获取当前登录用户的基本信息、角色和权限
    
    Returns:
        返回用户信息，格式为JSON:
        {msg: '登录成功~', code: 200, 
         user: {用户基本信息},
         roles: [...用户角色],
         permissions: [...权限列表]}
    """
    resources = []
    resourceTree = []

    resources += [res for org in current_user.organizations for res in org.resources if org.resources]
    resources += [res for role in current_user.roles for res in role.resources if role.resources]
    
    # remove repeat
    new_dict = dict()
    for obj in resources:
        if obj.ID not in new_dict:
            new_dict[obj.ID] = obj

    for resource in new_dict.values():
        resourceTree.append(resource.PERMS)

    return jsonify({'msg': '登录成功~', 'code': 200, \
        'user': {'userName': current_user.LOGINNAME, 'avatar': '', 'nickName': current_user.NAME, 'userId': current_user.ID}, \
        'roles': [role.NAME for role in current_user.roles], 'permissions': resourceTree})

@base.route('/system/user/profile', methods=['GET'])
@login_required
def syuser_profile():
    """获取用户个人信息
    
    获取当前登录用户的详细信息，包括部门和角色
    
    Returns:
        返回用户信息，格式为JSON:
        {msg: '操作成功', code: 200,
         data: 用户信息,
         postGroup: 所属部门,
         roleGroup: [...所属角色]}
    """
    return jsonify({'msg': '操作成功', 'code': 200, \
        'data': current_user.to_json(), \
        'postGroup': current_user.organizations[0].NAME if len(current_user.organizations) > 0 else '', \
        'roleGroup': [role.NAME for role in current_user.roles]})

@base.route('/system/user/profile', methods=['PUT'])
@login_required
def syuser_update_profile():
    """更新用户个人信息
    
    更新当前登录用户的基本信息，包括昵称、性别、邮箱、电话等
    
    Json Parameters:
        userId: 用户ID
        userName: 用户名
        nickName: 昵称，可选
        sex: 性别，可选
        email: 邮箱，可选
        phonenumber: 电话，可选
        
    Returns:
        返回操作结果 {code: 200, msg: '更新成功！'}
    """
    id = request.json['userId']
    userName = request.json['userName']
    user = User.query.get(id)

    user.UPDATEDATETIME = datetime.now()
    if 'nickName' in request.json: user.NAME = request.json['nickName'] 
    if 'sex' in request.json: user.SEX = request.json['sex']
    if 'email' in request.json: user.EMAIL = request.json['email']
    if 'phonenumber' in request.json: user.PHONENUMBER = request.json['phonenumber']

    db.session.add(user)

    return jsonify({'code': 200, 'msg': '更新成功！'})

@base.route('/system/user/authRole/<id>', methods=['GET'])
@login_required
def syuser_auth_role(id):
    """获取用户角色授权信息
    
    获取指定用户的角色授权信息，包括已分配和未分配的角色
    
    Args:
        id: 用户ID
        
    Returns:
        返回用户角色信息，格式为JSON:
        {code: 200, msg: '操作成功', 
         roles: [...所有角色列表], 
         user: 用户信息}
    """
    user = User.query.get(id)
    userRoles = [role for role in user.roles]
    allRoles = Role.query.all()
    for allRole in allRoles:
        for userRole in userRoles:
            if userRole.ID == allRole.ID:
                allRole.flag = True

    return jsonify({'code': 200, 'msg': '操作成功', 'roles': [role.to_json() for role in allRoles], 'user': user.to_json()})

@base.route('/base/syuser/export', methods=['POST'])
@login_required
def user_export():
    """导出用户数据
    
    将系统中的用户数据导出为CSV文件
    包含用户的登录名、姓名、创建时间、修改时间、性别等信息
    
    Returns:
        返回CSV格式的文件下载响应
    """
    rows = []
    rows.append(['登录名', '姓名', '创建时间', '修改时间', '性别'])

    users = User.query.all()
    for user in users:
        row = []
        row.append(user.LOGINNAME)
        row.append(user.NAME)
        row.append(user.CREATEDATETIME)
        row.append(user.UPDATEDATETIME)
        if user.SEX == '0':
            row.append('女')
        elif user.SEX == '1':
            row.append('男')
        rows.append(row)

    return excel.make_response_from_array(rows, "csv",
                                          file_name="user")


@base.route('/system/user/changeStatus', methods=['PUT'])
@login_required
@permission('system:user:edit')
def syuser_status_update():
    """更新用户状态
    
    更新指定用户的启用/禁用状态
    
    Json Parameters:
        userId: 用户ID
        status: 状态值
        
    Returns:
        返回操作结果 {code: 200, msg: '操作成功'}
    """
    user = User.query.get(request.json['userId'])

    if 'status' in request.json: user.STATUS = request.json['status']

    db.session.add(user)

    return jsonify({'code': 200, 'msg': '操作成功'})

