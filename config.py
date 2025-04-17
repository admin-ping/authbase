import os
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    基础配置类
    
    通用配置参数（可通过环境变量覆盖）：
    - SECRET_KEY: 应用密钥（默认：'hard to guess string'）
    - SQLALCHEMY_COMMIT_ON_TEARDOWN: 请求结束时自动提交数据库变更（默认：True）
    - FLASKY_MAIL_SUBJECT_PREFIX: 邮件主题前缀（默认：'[Flasky]'）
    - FLASKY_MAIL_SENDER: 邮件发送地址（默认：'example@example.com'）
    - FLASKY_ADMIN: 管理员邮箱（从环境变量获取）
    - SQLALCHEMY_TRACK_MODIFICATIONS: 跟踪对象修改（默认：True）
    - SQLALCHEMY_ENGINE_OPTIONS: 数据库引擎选项，包含连接预检机制
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'example@example.com'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """
    开发环境配置
    
    特定配置项：
    - DEBUG: 启用调试模式（默认：True）
    - MAIL_SERVER: SMTP服务器（默认：'smtp.qq.com'）
    - MAIL_PORT: SMTP端口（默认：587）
    - MAIL_USE_TLS: 启用TLS加密（默认：True）
    - MAIL_USERNAME: 邮箱用户名（从环境变量获取）
    - MAIL_PASSWORD: 邮箱密码（从环境变量获取）
    - SQLALCHEMY_DATABASE_URI: 数据库连接URI
      （默认：mysql://root:root@localhost/authbase）
    
    环境变量示例：
    export MAIL_USERNAME='your_email@qq.com'
    export MAIL_PASSWORD='your_email_password'
    """
    DEBUG = True
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI') or \
                              'mysql+mysqlconnector://root:root@127.0.0.1/authbase?charset=utf8&auth_plugin=mysql_native_password'


class TestingConfig(Config):
    """
    测试环境配置
    
    特定配置项：
    - TESTING: 启用测试模式（默认：False）
    - SQLALCHEMY_DATABASE_URI: SQLite测试数据库路径
      （默认：项目目录下的data-test.sqlite）
    
    建议通过环境变量覆盖配置：
    export TEST_DATABASE_URI='sqlite:////tmp/test.db'
    """
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    """
    生产环境配置
    
    特定配置项：
    - SQLALCHEMY_DATABASE_URI: 生产数据库连接URI
      （默认：项目目录下的data.sqlite）
    
    重要安全建议：
    1. 必须通过环境变量设置SECRET_KEY
    2. 数据库应使用生产级数据库（如MySQL/PostgreSQL）
    3. 禁用调试模式
    
    环境变量示例：
    export DATABASE_URI='mysql://user:password@production-db:3306/db_name'
    """
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
