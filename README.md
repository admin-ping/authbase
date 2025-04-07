# Port Knocking管理系统

## 项目概述
基于Flask+Vue实现的智能端口敲门认证系统，核心功能包含：
- 动态端口敲门序列认证（支持TCP/UDP混合协议）
- 敲门规则生命周期管理（创建/更新/删除）
- 基于时间窗口的敲门序列验证（支持开放端口超时时间配置）
- 安全令牌动态生成（HMAC-SHA256算法）
- 敲门成功后自动开启目标端口（支持动态ACL更新）
- 实时操作日志审计（记录完整敲门过程）
系统采用进程隔离架构，通过独立监听进程保障敲门服务稳定性，并与RBAC权限体系深度集成，提供企业级安全管控能力。

## 核心功能
- Port Knocking管理
- RBAC权限模型
- 组织机构树形管理
- 角色权限矩阵配置
- 资源路由自动注册
- 操作日志追踪
- 在线用户管理
- 数据字典管理

## 技术架构
### 后端技术栈
- **核心框架**: Flask 2.2.5
- **ORM**: Flask-SQLAlchemy 3.0.3
- **安全认证**: Flask-Login 0.6.2
- **数据库驱动**: mysql-connector-python 8.0.33
- **REST API**: Flask-RESTful 0.3.9

### 前端技术栈
- **核心框架**: Vue 2.6.14
- **UI组件库**: Element-UI 2.15.13
- **状态管理**: Vuex 3.6.2
- **构建工具**: Webpack 4

## 快速开始

### 环境要求
- Python 3.7+
- Node.js 14+
- MySQL 8.0+

### 数据库配置
1. 创建数据库
```sql
CREATE DATABASE authbase CHARACTER SET utf8mb4;
```
2. 修改配置文件 `config.py`：
```python
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://user:password@localhost:3306/authbase'
```
3. 初始化数据库
```bash
mysql -u root -p < db.sql
```


### 后端启动
```bash
# 安装依赖
pip install -r requirements.txt



# 启动开发服务器
flask --app start.py run
```

### 前端启动
```bash
cd ui
npm install
npm run dev
```

## 系统架构
```
├── app/                 # Flask应用核心
│   ├── models/         # 数据库模型
│   ├── routes/         # API路由模块
│   └── utils/          # 安全验证工具
├── ui/                 # Vue前端工程
│   ├── src/            
│   │   ├── api/        # 接口封装
│   │   └── views/      # 页面组件
├── config.py           # 后端配置
└── requirements.txt    # Python依赖
```

## 构建部署
```bash
# 生产环境构建
cd ui && npm run build

# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4  "start:create_app()"
```

## 注意事项
- 开发时自动忽略.pyc文件（已配置.gitignore）
- 生产环境请关闭DEBUG模式
- 数据库迁移请使用Flask-Migrate
- 在Windows环境下可测试除端口敲门外的全部功能
