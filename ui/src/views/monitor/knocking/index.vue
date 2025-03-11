<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryForm" :inline="true" v-show="showSearch">
      <el-form-item label="规则ID" prop="id">
        <el-input v-model="queryParams.id" placeholder="请输入规则ID" clearable size="small" />
      </el-form-item>
      <el-form-item label="端口序列" prop="portSequence">
        <el-input v-model="queryParams.portSequence" placeholder="请输入端口序列" clearable size="small" />
      </el-form-item>
      <el-form-item label="创建者" prop="createBy">
        <el-input v-model="queryParams.createBy" placeholder="请输入创建者" clearable size="small" />
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
          v-model="dateRange"
          size="small"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="el-icon-search" size="mini" @click="handleQuery">搜索</el-button>
        <el-button icon="el-icon-refresh" size="mini" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="el-icon-plus"
          size="mini"
          @click="handleAdd"
        >新增</el-button>
      </el-col>
      <right-toolbar :showSearch.sync="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="ruleList">
      <el-table-column label="规则ID" align="center" prop="id" />
      <el-table-column label="端口序列" align="center" prop="portSequence" />
      <el-table-column label="目标端口" align="center" prop="targetPort" />
      <el-table-column label="等待时间" align="center" prop="timeWindow">
        <template slot-scope="scope">
          {{ scope.row.timeWindow }}秒
        </template>
      </el-table-column>
      <el-table-column label="超时时间" align="center" prop="timeout">
        <template slot-scope="scope">
          {{ scope.row.timeout }}秒
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" prop="status">
        <template slot-scope="scope">
          <el-tag :type="scope.row.status === '1' ? 'success' : 'info'">
            {{ scope.row.status === '1' ? '正常' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建者" align="center" prop="createBy" />
      <el-table-column label="创建时间" align="center" prop="createTime" width="180">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" align="center" prop="updateTime" width="180">
        <template slot-scope="scope">
          <span>{{ parseTime(scope.row.updateTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template slot-scope="scope">
          <el-button
            size="mini"
            type="text"
            icon="el-icon-edit"
            @click="handleUpdate(scope.row)"
          >修改</el-button>
          <el-button
            size="mini"
            type="text"
            icon="el-icon-delete"
            @click="handleDelete(scope.row)"
          >删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total>0"
      :total="total"
      :page.sync="queryParams.pageNum"
      :limit.sync="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加或修改对话框 -->
    <el-dialog :title="title" :visible.sync="open" width="500px" append-to-body>
      <el-form ref="form" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="端口序列" prop="portSequence">
          <el-input v-model="form.portSequence" placeholder="请输入端口序列，格式：1201:TCP,2301:UDP,3401:TCP" />
        </el-form-item>
        <el-form-item label="目标端口" prop="targetPort">
          <el-input-number v-model="form.targetPort" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="等待时间" prop="timeWindow">
          <el-input-number v-model="form.timeWindow" :min="1" :max="3600" />
        </el-form-item>
        <el-form-item label="超时时间" prop="timeout">
          <el-input-number v-model="form.timeout" :min="1" :max="86400" />
        </el-form-item>
        <el-form-item label="认证密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入认证密码" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入内容" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="cancel">取 消</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { listRules, addRule, delRule, updateRule } from "@/api/monitor/knocking";

export default {
  name: "Knocking",
  data() {
    return {
      // 遮罩层
      loading: true,
      // 显示搜索条件
      showSearch: true,
      // 总条数
      total: 0,
      // 规则表格数据
      ruleList: [],
      // 弹出层标题
      title: "",
      // 是否显示弹出层
      open: false,
      // 日期范围
      dateRange: [],
      // 查询参数
      queryParams: {
        pageNum: 1,
        pageSize: 10,
        id: undefined,
        portSequence: undefined,
        createBy: undefined
      },
      // 表单参数
      form: {},
      // 表单校验
      rules: {
        portSequence: [
          { required: true, message: "端口序列不能为空", trigger: "blur" },
          { pattern: /^\d+:(TCP|UDP)(,\d+:(TCP|UDP))*$/, message: "端口序列格式不正确", trigger: "blur" }
        ],
        targetPort: [
          { required: true, message: "目标端口不能为空", trigger: "blur" }
        ],
        timeWindow: [
          { required: true, message: "等待时间不能为空", trigger: "blur" }
        ],
        timeout: [
          { required: true, message: "超时时间不能为空", trigger: "blur" }
        ],
        password: [
          { required: true, message: "认证密码不能为空", trigger: "blur" }
        ]
      }
    };
  },
  created() {
    this.getList();
  },
  methods: {
    /** 查询规则列表 */
    getList() {
      this.loading = true;
      listRules(this.addDateRange(this.queryParams, this.dateRange)).then(response => {
        this.ruleList = response.data;
        this.total = this.ruleList.length;
        this.loading = false;
      });
    },
    /** 取消按钮 */
    cancel() {
      this.open = false;
      this.reset();
    },
    /** 表单重置 */
    reset() {
      this.form = {
        portSequence: undefined,
        targetPort: undefined,
        timeWindow: 10,
        timeout: 20,
        password: undefined,
        remark: undefined
      };
      this.resetForm("form");
    },
    /** 搜索按钮操作 */
    handleQuery() {
      this.queryParams.pageNum = 1;
      this.getList();
    },
    /** 重置按钮操作 */
    resetQuery() {
      this.dateRange = [];
      this.resetForm("queryForm");
      this.handleQuery();
    },
    /** 新增按钮操作 */
    handleAdd() {
      this.reset();
      this.open = true;
      this.title = "添加敲门规则";
    },
    /** 修改按钮操作 */
    handleUpdate(row) {
      this.reset();
      this.form = row;
      this.open = true;
      this.title = "修改敲门规则";
    },
    /** 提交按钮 */
    submitForm() {
      this.$refs["form"].validate(valid => {
        if (valid) {
          if (this.form.id) {
            updateRule(this.form.id, this.form).then(response => {
              this.$modal.msgSuccess("修改成功");
              this.open = false;
              this.getList();
            });
          } else {
            addRule(this.form).then(response => {
              this.$modal.msgSuccess("新增成功");
              this.open = false;
              this.getList();
            });
          }
        }
      });
    },
    /** 删除按钮操作 */
    handleDelete(row) {
      this.$modal.confirm('是否确认删除规则？').then(function() {
        return delRule(row.id);
      }).then(() => {
        this.getList();
        this.$modal.msgSuccess("删除成功");
      }).catch(() => {});
    }
  }
};
</script>