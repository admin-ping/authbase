from ..base import base
from ..models import OnLine
from flask import render_template, request, jsonify
from sqlalchemy import asc
from sqlalchemy import desc
import flask_excel as excel
from flask_login import login_required
from .. import permission

@base.route('/monitor/logininfor/list', methods=['GET'])
@login_required
@permission('monitor:logininfor:list')
def grid_online():
    """获取登录历史列表
    
    支持按用户名、IP地址和登录类型过滤
    支持按创建时间范围过滤
    支持分页查询
    
    Query Parameters:
        userName: 用户名，可选，支持模糊查询
        ipaddr: IP地址，可选，支持模糊查询
        type: 登录类型，可选，精确匹配
        params[beginTime]: 开始时间，可选
        params[endTime]: 结束时间，可选
        page: 页码，默认1
        rows: 每页记录数，默认10
        
    Returns:
        返回登录历史列表，格式为JSON {total: 总数, rows: [...], code: 200}
    """
    # 构建过滤条件
    filters = []
    if request.args.get('userName'):
        filters.append(OnLine.LOGINNAME.like('%' + request.args.get('userName') + '%'))
    if request.args.get('ipaddr'):
        filters.append(OnLine.IP.like('%' + request.args.get('ipaddr') + '%'))
    if request.args.get('type'):
        filters.append(OnLine.TYPE == request.args.get('type'))
    if 'params[beginTime]' in request.args and 'params[endTime]' in request.args:
        filters.append(OnLine.CREATEDATETIME >  request.args['params[beginTime]'])
        filters.append(OnLine.CREATEDATETIME <  request.args['params[endTime]'])

    # 构建排序条件
    order_by = []
    if request.args.get('orderByColumn'):
        # 前端字段名到数据库字段名的映射
        field_mapping = {
            'loginTime': 'CREATEDATETIME',
            'userName': 'LOGINNAME',
            'ipaddr': 'IP',
            'type': 'TYPE'
        }
        # 获取排序字段名并转换为数据库字段名
        field_name = field_mapping.get(request.args.get('orderByColumn'))
        if field_name:
            if request.args.get('isAsc') == 'ascending':
                order_by.append(asc(getattr(OnLine, field_name)))
            else:
                order_by.append(desc(getattr(OnLine, field_name)))
    else:
        order_by.append(desc(OnLine.CREATEDATETIME))

    # 分页查询
    page = request.args.get('pageNum', 1, type=int)
    rows = request.args.get('pageSize', 10, type=int)
    pagination = OnLine.query.filter(*filters).order_by(*order_by).paginate(
        page=page, per_page=rows, error_out=False)
    onlines = pagination.items

    return jsonify({'total': OnLine.query.count(), 'rows': [online.to_json() for online in onlines], 'code': 200})

@base.route('/base/syonline/export', methods=['POST'])
@login_required
def online_export():
    """导出登录历史记录
    
    将所有登录历史记录导出为CSV文件
    包含登录名、IP地址、创建时间和登录类型等信息
    
    Returns:
        返回CSV文件下载响应
    """
    # 构建表头
    rows = []
    rows.append(['登录名', 'IP地址', '创建时间', '类别'])

    # 查询所有记录并格式化数据
    onlines = OnLine.query.all()
    for online in onlines:
        row = []
        row.append(online.LOGINNAME)
        row.append(online.IP)
        row.append(online.CREATEDATETIME)
        if online.TYPE == '0':
            row.append('注销系统')
        elif online.TYPE == '1':
            row.append('登录系统')
        rows.append(row)

    return excel.make_response_from_array(rows, "csv",
                                          file_name="online")