# coding:utf-8
from app import db
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime

# 角色资源关联表 - 用于建立角色和资源的多对多关系
role_resource_table = db.Table('SYROLE_SYRESOURCE', db.metadata,
                               db.Column('SYROLE_ID', db.String, db.ForeignKey('SYROLE.ID')),
                               db.Column('SYRESOURCE_ID', db.String, db.ForeignKey('SYRESOURCE.ID')))

# 角色组织关联表 - 用于建立角色和组织机构的多对多关系
role_organization_table = db.Table('SYROLE_SYORGANIZATION', db.metadata,
                               db.Column('SYROLE_ID', db.String, db.ForeignKey('SYROLE.ID')),
                               db.Column('SYORGANIZATION_ID', db.String, db.ForeignKey('SYORGANIZATION.ID')))

class Role(db.Model, UserMixin):
    """角色模型类
    
    用于管理系统中的角色信息，包括角色的基本属性、资源权限和组织权限
    可以关联多个资源和组织机构，实现权限的分配和管理
    """
    __tablename__ = 'SYROLE'  # 数据库表名
    ID = db.Column(db.Integer, primary_key=True)  # 角色ID，主键
    CREATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间
    UPDATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 更新时间
    NAME = db.Column(db.String(100))  # 角色名称
    DESCRIPTION = db.Column(db.String(200))  # 角色描述
    ICONCLS = db.Column(db.String(100))  # 图标样式类
    SEQ = db.Column(db.Integer)  # 显示顺序
    ROLEKEY = db.Column(db.String(100))  # 角色权限字符串
    DATASCOPE = db.Column(db.Integer)  # 数据范围（1：全部数据权限 2：自定数据权限 3：本部门数据权限 4：本部门及以下数据权限）
    STATUS = db.Column(db.String(10))  # 角色状态（0正常 1停用）

    # 角色可访问的资源列表，多对多关系
    resources = db.relationship('Resource',
                                secondary=role_resource_table,
                                backref=db.backref('roles', lazy='dynamic'))

    # 角色关联的部门列表，多对多关系
    depts = db.relationship('Organization',
                                secondary=role_organization_table,
                                backref=db.backref('roles', lazy='dynamic'))
    def get_id(self):
        """获取角色ID
        
        Returns:
            str: 角色ID字符串
        """
        return str(self.ID)

    def to_dict(self):
        """将角色对象转换为字典格式
        
        Returns:
            dict: 包含角色所有非私有属性的字典
        """
        return dict([(k, getattr(self, k)) for k in self.__dict__.keys() if not k.startswith("_")])

    def __repr__(self):
        """返回角色的字符串表示
        
        用于调试和日志输出
        
        Returns:
            str: 包含角色名称、描述、图标和序号的字符串表示
        """
        return '<Role name:%r description:%r iconCls:%r seq:%r>\n'  \
             %(self.NAME, self.DESCRIPTION, self.ICONCLS, self.SEQ)

    def to_json(self):
        """将角色对象转换为JSON格式
        
        用于API接口返回数据
        
        Returns:
            dict: 包含角色所有字段的JSON对象
        """
        json = {
            'roleId': self.ID,
            'createTime': self.CREATEDATETIME.strftime('%Y-%m-%d %H:%M:%S'),
            'updateTime': self.UPDATEDATETIME.strftime('%Y-%m-%d %H:%M:%S'),
            'roleName': self.NAME,
            'remark': self.DESCRIPTION,
            'iconCls': self.ICONCLS,
            'roleSort': self.SEQ,
            'status': self.STATUS,
            'roleKey': self.ROLEKEY,
            'dataScope': self.DATASCOPE
        }

        # 如果角色有标记属性，添加到JSON中
        if hasattr(self, 'flag'):
            json['flag'] = self.flag

        return json
