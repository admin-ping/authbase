from .. import db
from datetime import datetime

class KnockingRule(db.Model):
    """端口敲门规则模型
    
    该模型用于存储和管理端口敲门认证的规则配置，包括端口序列、目标端口、时间窗口等信息。
    端口敲门是一种通过按特定顺序访问一系列端口来获取访问权限的安全机制。
    """
    __tablename__ = 'sys_knocking_rule'
    
    id = db.Column(db.String(32), primary_key=True)  # 规则ID，主键
    port_sequence = db.Column(db.String(255), nullable=False, comment='端口序列')  # 敲门端口序列，格式如："1201:TCP,2301:UDP,3401:TCP"
    target_port = db.Column(db.Integer, nullable=False, comment='目标端口')  # 成功认证后开放的目标端口
    time_window = db.Column(db.Integer, nullable=False, comment='等待时间(秒)')  # 端口敲门序列的最大完成时间窗口
    timeout = db.Column(db.Integer, nullable=False, comment='超时时间(秒)')  # 认证成功后的会话超时时间
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希')  # 认证密码的哈希值
    status = db.Column(db.String(1), nullable=False, default='1', comment='状态（0停用 1正常）')  # 规则状态
    create_by = db.Column(db.String(64), nullable=True, comment='创建者')  # 规则创建人
    create_time = db.Column(db.DateTime, nullable=True, default=datetime.now, comment='创建时间')  # 规则创建时间
    update_by = db.Column(db.String(64), nullable=True, comment='更新者')  # 规则更新人
    update_time = db.Column(db.DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')  # 规则更新时间
    remark = db.Column(db.String(500), nullable=True, comment='备注')  # 规则备注说明
    
    def to_json(self):
        """将规则对象转换为JSON格式
        
        Returns：
        - 时间字段格式：YYYY-MM-DD HH:MM:SS
        - 状态字段值：0表示停用，1表示正常
        """
        json_data = {
            'id': self.id,
            'portSequence': self.port_sequence,
            'targetPort': self.target_port,
            'timeWindow': self.time_window,
            'timeout': self.timeout,
            'status': self.status,
            'createBy': self.create_by,
            'createTime': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'updateBy': self.update_by,
            'updateTime': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'remark': self.remark
        }
        return json_data