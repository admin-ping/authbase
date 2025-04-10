from ..base import base
from flask import render_template
from flask_login import login_user, logout_user, login_required, \
    current_user
from flask import g, jsonify
from ..models import Resource, Organization, ResourceType
from sqlalchemy import text

def setAccessable(resource, permitedIDList):
    """递归设置资源的可访问性

    Args:
        resource: Resource对象，需要设置访问权限的资源
        permitedIDList: list，允许访问的资源ID列表

    该函数会递归遍历资源树，如果某个资源的ID不在允许访问的列表中，
    则将其hidden属性设置为True，表示该资源对当前用户不可见。
    """
    if resource.ID not in permitedIDList:
        resource.HIDDEN = True
    
    for child in resource.children:
        setAccessable(child, permitedIDList)

@base.route('/getRouters')
@login_required
def getRouters():
    """获取当前用户可访问的路由菜单

    该接口用于获取当前登录用户可以访问的所有路由菜单信息。
    首先获取用户所属组织和角色下的所有资源权限，
    然后过滤出用户有权访问的资源，最后转换为前端路由格式返回。

    Returns:
        JSON格式的响应，包含用户可访问的路由菜单数据
        {msg: 操作结果信息, code: 状态码, data: 路由菜单数组}
    """
    # 获取用户所属组织和角色的所有资源权限
    resources = []
    resources += [res for org in current_user.organizations for res in org.resources if org.resources]
    resources += [res for role in current_user.roles for res in role.resources if role.resources]
    
    ids = [res.ID for res in resources]

    #allResources = Resource.query.filter(
    #    text("FIND_IN_SET(ID, :ids) > 0")).params(ids = ','.join(ids)) .all()
    
    allResources = Resource.query.join(ResourceType, Resource.type).filter(
        Resource.SYRESOURCE_ID == None).order_by(Resource.SEQ.asc()).all()
    # filter resource not allowed
    for res in allResources:
       setAccessable(res, ids)

    json = [res.to_router_json() for res in allResources]

    return jsonify({'msg': '操作成功', 'code': 200, "data": json})    


    # return jsonify({'msg': '操作成功', 'code': 200, "data":[{"name":"System","path":"/system","hidden":False,"redirect":"noRedirect","component":"Layout","alwaysShow":True,"meta":{"title":"系统管理","icon":"system","noCache":False,"link":''},"children":[{"name":"User","path":"user","hidden":False,"component":"system/user/index","meta":{"title":"用户管理","icon":"user","noCache":False,"link":''}},{"name":"Role","path":"role","hidden":False,"component":"system/role/index","meta":{"title":"角色管理","icon":"peoples","noCache":False,"link":''}},{"name":"Menu","path":"menu","hidden":False,"component":"system/menu/index","meta":{"title":"菜单管理","icon":"tree-table","noCache":False,"link":''}},{"name":"Dept","path":"dept","hidden":False,"component":"system/dept/index","meta":{"title":"部门管理","icon":"tree","noCache":False,"link":''}},{"name":"Log","path":"log","hidden":False,"redirect":"noRedirect","component":"ParentView","alwaysShow":True,"meta":{"title":"日志管理","icon":"log","noCache":False,"link":''},"children":[{"name":"Operlog","path":"operlog","hidden":False,"component":"monitor/operlog/index","meta":{"title":"操作日志","icon":"form","noCache":False,"link":''}},{"name":"Logininfor","path":"logininfor","hidden":False,"component":"monitor/logininfor/index","meta":{"title":"登录日志","icon":"logininfor","noCache":False,"link":''}}]}]}]})
