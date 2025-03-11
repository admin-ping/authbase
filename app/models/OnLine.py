from app import db
from datetime import datetime

# 在线用户模型类，用于记录和管理系统中当前在线的用户信息
class OnLine(db.Model):
    # 指定数据库表名
    __tablename__ = 'SYONLINE'
    # 用户在线记录的唯一标识符
    ID = db.Column(db.String(36), primary_key=True)
    # 用户登录时间，自动设置为当前时间
    CREATEDATETIME = db.Column(db.DateTime, index=True, default=datetime.now)
    # 用户登录名
    LOGINNAME = db.Column(db.String(100))
    # 用户登录IP地址
    IP = db.Column(db.String(100))
    # 用户登录类型，使用单字符表示不同的登录方式
    TYPE = db.Column(db.String(1))
    # 获取在线记录的唯一标识符
    def get_id(self):
        return str(self.ID)
    # 返回在线用户记录的字符串表示
    def __repr__(self):
        return '<Oneline %r>\n' %(self.LOGINNAME)
    # 将在线用户记录转换为JSON格式，用于API响应
    def to_json(self):
        return {
            'infoId': self.ID,
            'loginTime': self.CREATEDATETIME.strftime('%Y-%m-%d %H:%M:%S'),
            'userName': self.LOGINNAME,
            'ipaddr': self.IP,
            'type': self.TYPE
        }