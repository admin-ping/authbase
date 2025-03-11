from app import db
from flask_login import UserMixin, AnonymousUserMixin
from datetime import datetime


class ResourceType(db.Model, UserMixin):
    """资源类型模型类
    用于管理系统中各种资源的类型定义，如菜单、按钮等
    """
    __tablename__ = 'SYRESOURCETYPE'
    ID = db.Column(db.String(36), primary_key=True)  # 资源类型ID，主键
    CREATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间
    UPDATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)  # 更新时间
    NAME = db.Column(db.String(100))  # 资源类型名称
    DESCRIPTION = db.Column(db.String(200))  # 资源类型描述

    # 与Resource模型的一对多关系，一个资源类型可以对应多个资源
    resources = db.relationship('Resource', backref='type', lazy='dynamic')

    def to_json(self):
        """将资源类型对象转换为JSON格式
        用于API接口返回数据
        """
        return {
            'id': self.ID,
            'createdatetime': self.CREATEDATETIME,
            'updatedatetime': self.UPDATEDATETIME,
            'name': self.NAME,
            'description': self.DESCRIPTION
        }

    def __repr__(self):
        """返回资源类型对象的字符串表示
        用于调试和日志输出
        """
        return '<ResourceType %r>\n' %(self.NAME)