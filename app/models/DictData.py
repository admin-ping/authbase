from app import db
from datetime import datetime

class DictData(db.Model):
    """字典数据表模型
    用于存储系统中各种字典类型的具体数据项，如状态码、业务类型等
    """
    __tablename__ = 'SYS_DICT_DATA'
    dict_code = db.Column(db.Integer, primary_key=True)  # 字典编码，主键
    dict_sort = db.Column(db.Integer)  # 字典排序
    dict_label = db.Column(db.String(100))  # 字典标签
    dict_value = db.Column(db.String(100))  # 字典键值
    dict_type = db.Column(db.String(100), db.ForeignKey('SYS_DICT_TYPE.dict_type'))  # 字典类型，外键关联字典类型表
    css_class = db.Column(db.String(100))  # 样式属性
    list_class = db.Column(db.String(100))  # 表格回显样式
    is_default = db.Column(db.Integer)  # 是否默认（1是 0否）
    status = db.Column(db.Integer)  # 状态（0停用 1正常）
    create_by = db.Column(db.String(64))  # 创建者
    create_time = db.Column(db.DATETIME, default=datetime.now)  # 创建时间
    update_by = db.Column(db.String(64))  # 更新者
    update_time = db.Column(db.DATETIME, default=datetime.now)  # 更新时间
    remark = db.Column(db.String(500))  # 备注

    def to_json(self):
        """将字典数据对象转换为JSON格式
        用于API接口返回数据
        """
        return {
            'dictCode': self.dict_code,
            'dictSort': self.dict_sort,
            'dictLabel': self.dict_label,
            'dictValue': self.dict_value,
            'dictType': self.dict_type,
            'cssClass': self.css_class,
            'listClass': self.list_class,
            'isDefault': self.is_default,
            'status': self.status,
            'createBy': self.create_by,
            'createTime': self.create_time,
            'updateBy': self.update_by,
            'updateTime': self.update_time,
            'remark': self.remark
        }

    def __repr__(self):
        """返回字典数据对象的字符串表示
        用于调试和日志输出
        """
        return '<DictData %r>\n' %(self.dict_label)