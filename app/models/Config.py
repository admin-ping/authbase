from app import db
from datetime import datetime

class Config(db.Model):
    """系统配置表模型
    用于存储和管理系统级别的配置项，如系统参数、业务配置等
    """
    __tablename__ = 'SYS_CONFIG'
    config_id = db.Column(db.Integer, primary_key=True)  # 配置ID，主键
    config_name = db.Column(db.String(100))  # 配置名称
    config_key = db.Column(db.String(100))   # 配置键名
    config_value = db.Column(db.String(500))  # 配置键值
    config_type = db.Column(db.Integer)  # 配置类型（0系统配置 1业务配置）
    create_by = db.Column(db.String(64))  # 创建者
    create_time = db.Column(db.DATETIME, default=datetime.now)  # 创建时间
    update_by = db.Column(db.String(64))  # 更新者
    update_time = db.Column(db.DATETIME, default=datetime.now)  # 更新时间
    remark = db.Column(db.String(500))  # 备注说明

    def to_json(self):
        """将配置对象转换为JSON格式
        用于API接口返回数据
        """
        return {
            'configId': self.config_id,
            'configName': self.config_name,
            'configKey': self.config_key,
            'configValue': self.config_value,
            'configType': self.config_type,
            'createBy': self.create_by,
            'createTime': self.create_time,
            'updateBy': self.update_by,
            'updateTime': self.update_time,
            'remark': self.remark,
        }

    def __repr__(self):
        """返回配置对象的字符串表示
        用于调试和日志输出
        """
        return '<Config %r>\n' %(self.config_name)