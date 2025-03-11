import request from '@/utils/request'

// 查询敲门规则列表
export function listRules(query) {
  return request({
    url: '/listrules',
    method: 'get',
    params: query
  })
}

// 添加敲门规则
export function addRule(data) {
  return request({
    url: '/addrules',
    method: 'post',
    data: data
  })
}

// 删除敲门规则
export function delRule(ruleId) {
  return request({
    url: '/rules/' + ruleId,
    method: 'delete'
  })
}

// 修改敲门规则
export function updateRule(ruleId, data) {
  return request({
    url: '/rules/' + ruleId,
    method: 'put',
    data: data
  })
}