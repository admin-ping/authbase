from app import db
from datetime import datetime

# 字典类型管理模型，用于维护系统中各种字典类型的基本信息
class DictType(db.Model):
    __tablename__ = 'SYS_DICT_TYPE'
    # 字典类型ID，主键
    dict_id = db.Column(db.Integer, primary_key=True)
    # 字典类型名称
    dict_name = db.Column(db.String(100))
    # 字典类型标识
    dict_type = db.Column(db.String(100))
    # 状态（0正常 1停用）
    status = db.Column(db.Integer)
    # 创建者
    create_by = db.Column(db.String(64))
    # 创建时间
    create_time = db.Column(db.DATETIME, default=datetime.now)
    # 更新者
    update_by = db.Column(db.String(64))
    # 更新时间
    update_time = db.Column(db.DATETIME, default=datetime.now)
    # 备注信息
    remark = db.Column(db.String(500))

    # 与字典数据表建立一对多关系
    data_list =  db.relationship('DictData', backref='type', lazy='dynamic')

    # 将对象转换为JSON格式，用于API响应
    def to_json(self):
        return {
            'dictId': self.dict_id,
            'dictName': self.dict_name,
            'dictType': self.dict_type,
            'status': self.status,
            'createBy': self.create_by,
            'createTime': self.create_time,
            'updateBy': self.update_by,
            'updateTime': self.update_time,
            'remark': self.remark,
        }

    # 返回字典类型的字符串表示
    def __repr__(self):
        return '<DictType %r>\n' %(self.dict_name)