// 导入必要的依赖模块
const { run } = require('runjs')
const chalk = require('chalk')
const config = require('../vue.config.js')

// 获取命令行参数
const rawArgv = process.argv.slice(2)
const args = rawArgv.join(' ')

// 判断是否需要启动预览服务器
if (process.env.npm_config_preview || rawArgv.includes('--preview')) {
  // 检查是否需要生成报告
  const report = rawArgv.includes('--report')

  // 执行构建命令
  run(`vue-cli-service build ${args}`)

  // 设置预览服务器配置
  const port = 9526
  const publicPath = config.publicPath

  // 创建静态文件服务器
  var connect = require('connect')
  var serveStatic = require('serve-static')
  const app = connect()

  // 配置静态资源服务
  app.use(
    publicPath,
    serveStatic('./dist', {
      index: ['index.html', '/']
    })
  )

  // 启动预览服务器
  app.listen(port, function () {
    console.log(chalk.green(`> Preview at  http://localhost:${port}${publicPath}`))
    if (report) {
      console.log(chalk.green(`> Report at  http://localhost:${port}${publicPath}report.html`))
    }

  })
} else {
  // 如果不需要预览，直接执行构建命令
  run(`vue-cli-service build ${args}`)
}
