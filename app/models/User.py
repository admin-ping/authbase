from app import db, loginmanager
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime

# 用户加载回调函数，用于从数据库加载用户对象
@loginmanager.user_loader
def load_user(user_id):
    return User.query.filter(User.ID == user_id).first()

# 用户-组织机构关联表，用于建立用户和组织机构的多对多关系
user_organization_table = db.Table('SYUSER_SYORGANIZATION', db.Model.metadata
                                   , db.Column('SYUSER_ID', db.String, db.ForeignKey('SYUSER.ID'))
                                   , db.Column('SYORGANIZATION_ID', db.String, db.ForeignKey('SYORGANIZATION.ID')))

# 用户-角色关联表，用于建立用户和角色的多对多关系
user_role_table = db.Table('SYUSER_SYROLE', db.Model.metadata
                           , db.Column('SYUSER_ID', db.String, db.ForeignKey('SYUSER.ID'))
                           , db.Column('SYROLE_ID', db.String, db.ForeignKey('SYROLE.ID')))

class User(db.Model, UserMixin):
    """用户模型类
    
    用于管理系统中的用户信息，包括用户的基本信息、认证信息和权限关系
    可以关联多个组织机构和角色，实现灵活的权限管理
    """
    __tablename__ = 'SYUSER'  # 数据库表名
    ID = db.Column(db.String(36), primary_key=True)  # 用户ID，主键
    CREATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间
    UPDATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 更新时间
    LOGINNAME = db.Column(db.String(100), unique=True, index=True)  # 登录名，唯一
    PWD = db.Column(db.String(100))  # 密码
    NAME = db.Column(db.String(100))  # 用户姓名
    SEX = db.Column(db.String(1))  # 性别
    AGE = db.Column(db.Integer)  # 年龄
    PHOTO = db.Column(db.String(200))  # 头像照片URL
    EMPLOYDATE = db.Column(db.DATETIME, default=datetime.now)  # 入职日期
    EMAIL = db.Column(db.String(50))  # 电子邮箱
    PHONENUMBER = db.Column(db.String(11))  # 手机号码
    STATUS = db.Column(db.String(10))  # 用户状态

    # 用户所属组织机构，多对多关系
    organizations = db.relationship('Organization',
                                    secondary=user_organization_table,
                                    backref=db.backref('users', lazy='dynamic'),)

    # 用户拥有的角色，多对多关系
    roles = db.relationship('Role',
                            secondary=user_role_table,
                            backref=db.backref('users', lazy='dynamic'),
                            lazy="dynamic")

    def get_id(self):
        """获取用户ID
        
        用于Flask-Login用户认证
        
        Returns:
            str: 用户ID字符串
        """
        return str(self.ID)

    def have_permission(self, url):
        """检查用户是否有访问指定URL的权限
        
        通过用户的角色和组织机构关联的资源来判断权限
        
        Args:
            url: 要检查权限的URL
            
        Returns:
            bool: 如果有权限返回True，否则返回False
        """
        permissions = []
        for role in self.roles:
            permissions.extend([resource for resource in role.resources])

        if filter(lambda x: x.URL == url, permissions):
            return True

        permissions = []
        for organization in self.organizations:
            permissions.extend([resource for resource in organization.resources])

        return filter(lambda x: x.NAME == url, permissions)
        
    def __repr__(self):
        """返回用户对象的字符串表示
        
        用于调试和日志输出
        
        Returns:
            str: 包含用户姓名的字符串表示
        """
        return '<User %r>\n' %(self.NAME)

    def to_json(self):
        """将用户对象转换为JSON格式
        
        用于API接口返回数据
        包含用户的基本信息、部门信息和角色信息
        
        Returns:
            dict: 包含用户所有字段的JSON对象
        """
        json = {
            'userId': self.ID,
            'createTime': self.CREATEDATETIME.strftime('%Y-%m-%d %H:%M:%S'),
            'updateTime': self.UPDATEDATETIME.strftime('%Y-%m-%d %H:%M:%S'),
            'userName': self.LOGINNAME,
            'nickName': self.NAME,
            'sex': self.SEX,
            'age': self.AGE,
            "status": self.STATUS,
            'photo': self.PHOTO,
            'email': self.EMAIL,
            'phonenumber': self.PHONENUMBER
            #'employdate': self.EMPLOYDATE.strftime('%Y-%m-%d %H:%M:%S'),
        }

        if len(self.organizations) > 0:
            json['dept']  = self.organizations[0].to_json()
            json['deptId'] = self.organizations[0].ID

        if len(self.roles.all()) > 0:
            json['roles'] = [role.to_json() for role in self.roles.all()]

        return json