from app import db
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime
from flask import jsonify


class Resource(db.Model, UserMixin):
    """系统资源模型类
    
    用于管理系统中的菜单、按钮等资源
    支持树形结构的资源关系
    可以被角色和组织机构引用进行权限管理
    """
    __tablename__ = 'SYRESOURCE'
    __mapper_args__ = {
     #"order_by": 'SEQ'
    }
    # 资源ID，主键
    ID = db.Column(db.String(36), primary_key=True)
    # 创建时间
    CREATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)
    # 更新时间
    UPDATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)
    # 资源名称
    NAME = db.Column(db.String(100))
    # 资源URL
    URL = db.Column(db.String(200))
    # 路由路径
    PATH = db.Column(db.String(200))
    # 权限标识
    PERMS = db.Column(db.String(150))
    # 资源描述
    DESCRIPTION = db.Column(db.String(200))
    # 图标样式类
    ICONCLS = db.Column(db.String(100))
    # 显示顺序
    SEQ = db.Column(db.Integer)
    # 打开方式
    TARGET = db.Column(db.String(100))

    # 资源类型ID，外键关联SYRESOURCETYPE表
    SYRESOURCETYPE_ID = db.Column(db.String, db.ForeignKey('SYRESOURCETYPE.ID'))

    # 父资源ID，外键关联自身
    SYRESOURCE_ID = db.Column(db.String, db.ForeignKey('SYRESOURCE.ID'))

    # 父资源关系
    parent = db.relationship('Resource', remote_side=[ID], backref='resource', uselist=False)

    # 子资源列表
    children = db.relationship('Resource')

    # 资源状态
    STATUS = db.Column(db.String(10))

    # 是否隐藏
    HIDDEN = False

    def get_id(self):
        """获取资源ID
        
        Returns:
            str: 资源ID字符串
        """
        return str(self.ID)

    def to_json(self):
        """将资源信息转换为JSON格式
        
        用于前端菜单管理功能的数据展示
        
        Returns:
            dict: 包含资源所有字段的JSON对象
        """
        return {
            'menuId': self.ID,
            'createTime': self.CREATEDATETIME,
            'updateTime': self.UPDATEDATETIME,
            'menuName': self.NAME,
            'component': self.URL,
            'description': self.DESCRIPTION,
            'icon': self.ICONCLS,
            'orderNum': self.SEQ,
            'target': self.TARGET,
            'parentId': self.get_pid(),
            'syresourcetype': self.get_type_json(),
            'status': self.STATUS,
            'visible': '0',
            'isFrame': '1',
            'path': self.PATH,
            'perms': self.PERMS,
            'isCache': '1',
            # 类型（M目录 C菜单 F按钮）
            'menuType': 'F' if self.SYRESOURCETYPE_ID == '1' else 'C' if self.SYRESOURCETYPE_ID == '0' else 'M'
        }

    def to_tree_select_json(self):
        """将资源信息转换为树形选择控件需要的JSON格式
        
        用于前端树形选择控件的数据展示
        
        Returns:
            dict: 包含id、label和children的树形结构JSON对象
        """
        return {
            'id': self.ID,
            'label': self.NAME,
            'children': [res.to_tree_select_json() for res in self.children]
        }

    def to_router_json(self):
        """将资源信息转换为前端路由需要的JSON格式
        
        用于生成前端Vue Router的路由配置
        处理菜单的层级关系、重定向、组件等信息
        
        Returns:
            dict: 符合Vue Router格式的路由配置对象
        """
        router = {
            'name': self.PATH.capitalize() if self.PATH else self.NAME.capitalize(),
            'path': self.PATH if self.PATH else '/' + self.NAME.lower(),
            'hidden': self.HIDDEN,
            'redirect': 'noRedirect',
            'component': self.URL,
            'alwaysShow': True,
            'meta': {
                'title': self.NAME,
                'icon': self.ICONCLS,
                'noCache': False,
                'link':''
            },
            'children': [
                res.to_router_json() for res in self.children if res.type.ID == '3' or res.type.ID == '0'
            ]
        }

        if not router['children']:
            del router['children']
            del router['redirect']
            del router['alwaysShow']
        if not router['component']:
            router['component'] = 'Layout'

        return router

    def to_menu_json(self):
        """将资源信息转换为菜单JSON格式
        
        用于传统树形菜单的数据展示
        
        Returns:
            dict: 包含菜单基本信息的JSON对象
        """
        return {
            'id': self.ID,
            'iconCls': self.ICONCLS,
            'pid': self.get_pid(),
            'state': 'open',
            'checked': False,
            'attributes': {
                'target': self.TARGET,
                'url': self.URL
            },
            'text': self.NAME
        }

    def get_pid(self):
        """获取父资源ID
        
        Returns:
            str: 父资源ID，如果没有父资源则返回空字符串
        """
        if self.parent:
            return self.parent.ID
        return ''

    def get_type_json(self):
        """获取资源类型的JSON格式
        
        Returns:
            dict: 资源类型的JSON对象，如果没有类型则返回空对象
        """
        if self.type:
            return self.type.to_json()
        return {}

    def __repr__(self):
        """返回资源的字符串表示
        
        Returns:
            str: 包含资源名称和URL的字符串表示
        """
        return '<Resource name:%r url:%r>\n' %(self.NAME, self.URL)