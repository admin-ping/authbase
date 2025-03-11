from app import db
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime

# 组织机构与资源的多对多关联表
organization_resource_table = db.Table('SYORGANIZATION_SYRESOURCE', db.metadata,
                                       db.Column('SYRESOURCE_ID', db.String, db.ForeignKey('SYRESOURCE.ID')),
                                       db.Column('SYORGANIZATION_ID', db.String, db.ForeignKey('SYORGANIZATION.ID')))


class Organization(db.Model, UserMixin):
    """组织机构模型类
    
    用于管理系统中的部门、机构等组织结构信息
    支持树形结构的组织关系
    可以关联资源进行权限管理
    """
    __tablename__ = 'SYORGANIZATION'
    ID = db.Column(db.String(36), primary_key=True)  # 主键ID
    CREATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间
    UPDATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 更新时间
    NAME = db.Column(db.String(200))  # 组织名称
    ADDRESS = db.Column(db.String(200))  # 组织地址
    CODE = db.Column(db.String(200))  # 组织编码
    ICONCLS = db.Column(db.String(100))  # 图标样式类
    SEQ = db.Column(db.Integer)  # 显示顺序
    LEADER = db.Column(db.String(20))  # 负责人
    PHONE = db.Column(db.String(11))  # 联系电话
    EMAIL = db.Column(db.String(50))  # 电子邮箱
    STATUS = db.Column(db.String(10))  # 组织状态

    # 组织可访问的资源列表，多对多关系
    resources = db.relationship('Resource',
                                secondary=organization_resource_table,
                                backref=db.backref('organizations', lazy='dynamic'))

    # 父组织ID，用于构建组织树形结构
    SYORGANIZATION_ID = db.Column(db.String, db.ForeignKey('SYORGANIZATION.ID'))

    # 父组织关系
    parent = db.relationship('Organization', remote_side=[ID], backref='organization', uselist=False)

    # 子组织列表
    children = db.relationship('Organization')

    def to_json(self):
        """将组织信息转换为JSON格式
        
        Returns:
            dict: 包含组织所有字段的JSON对象
        """
        return {
            'deptId': self.ID,
            'createTime': self.CREATEDATETIME,
            'updateTime': self.UPDATEDATETIME,
            'deptName': self.NAME,
            'address': self.ADDRESS,
            'code': self.CODE,
            'iconCls': self.ICONCLS,
            'orderNum': self.SEQ,
            'parentId': self.get_pid(),
            'leader': self.LEADER,
            'phone': self.PHONE,
            'email': self.EMAIL,
            'status': self.STATUS,
            'children': [
                org.to_json() for org in self.children
            ]
        }
    
    def to_tree_select_json(self):
        """将组织信息转换为树形选择控件需要的JSON格式
        
        Returns:
            dict: 包含id、label和children的树形结构JSON对象
        """
        return {
            'id': self.ID,
            'label': self.NAME,
            'children': [org.to_tree_select_json() for org in self.children]
        }

    def get_pid(self):
        """获取父组织ID
        
        Returns:
            str: 父组织ID，如果没有父组织则返回空字符串
        """
        if self.parent:
            return self.parent.ID
        return ''

    def get_id(self):
        """获取组织ID
        
        Returns:
            str: 组织ID字符串
        """
        return str(self.ID)

    def __repr__(self):
        """返回组织的字符串表示
        
        Returns:
            str: 包含组织名称的字符串表示
        """
        return '<Organization %r>\n' %(self.NAME)