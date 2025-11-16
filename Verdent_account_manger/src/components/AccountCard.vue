<script setup lang="ts">
import { ref, computed } from 'vue'
import { invoke } from '@tauri-apps/api/core'

interface Account {
  id: string
  email: string
  password: string
  register_time: string
  expire_time?: string      // 订阅到期时间 (从 currentPeriodEnd 转换)
  status: string
  token?: string
  quota_remaining?: string  // 改为 string 以支持小数
  quota_used?: string       // 新增: 已消耗额度
  quota_total?: string      // 改为 string 以支持小数
  subscription_type?: string
  trial_days?: number       // 新增: 试用天数
  current_period_end?: number  // Unix时间戳(秒)
  auto_renew?: boolean      // 新增: 是否自动续订
  token_expire_time?: string  // 新增: Token 过期时间 (从 JWT exp 解析)
  last_updated?: string
}

const props = defineProps<{
  account: Account
  originalEmail?: string
  isSelected?: boolean
  isCurrent?: boolean
}>()

const emit = defineEmits<{
  refresh: [id: string]
  edit: [account: Account]
  delete: [id: string]
  showToast: [message: string, type: 'success' | 'error' | 'warning' | 'info']
  toggleSelection: [id: string]
  setCurrent: [id: string]
}>()

const showPassword = ref(false)
const isHovered = ref(false)

const registerDate = computed(() => {
  const date = new Date(props.account.register_time)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const expireDate = computed(() => {
  if (!props.account.expire_time) return '未知'
  const date = new Date(props.account.expire_time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

// 计算到期剩余天数
const daysUntilExpire = computed(() => {
  if (!props.account.expire_time) return null
  const now = new Date()
  const expireDate = new Date(props.account.expire_time)
  const diffTime = expireDate.getTime() - now.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
})

// 到期时间的颜色样式
const expireColor = computed(() => {
  const days = daysUntilExpire.value
  if (days === null) return '#8e8e93'
  if (days < 0) return '#ff3b30'  // 已过期 - 红色
  if (days <= 3) return '#ff9500'  // 3天内 - 橙色
  return '#34c759'  // 正常 - 绿色
})

// 订阅周期结束时间格式化
const subscriptionEndDate = computed(() => {
  if (!props.account.current_period_end) return '未知'
  // current_period_end 是秒级时间戳,转换为毫秒
  const date = new Date(props.account.current_period_end * 1000)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

// 订阅周期结束时间标签
const subscriptionEndLabel = computed(() => {
  return props.account.auto_renew ? '下次续订时间' : '订阅周期结束时间'
})

// Token 过期时间格式化
const tokenExpireDate = computed(() => {
  if (!props.account.token_expire_time) return '未知'
  const date = new Date(props.account.token_expire_time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const quotaPercentage = computed(() => {
  if (!props.account.quota_remaining || !props.account.quota_total) return 0
  const remaining = parseFloat(props.account.quota_remaining)
  const total = parseFloat(props.account.quota_total)
  if (isNaN(remaining) || isNaN(total) || total === 0) return 0
  return Math.round((remaining / total) * 100)
})

// 订阅类型的颜色
const subscriptionColor = computed(() => {
  switch (props.account.subscription_type) {
    case 'Free': return '#8e8e93'
    case 'Starter': return '#007aff'
    case 'Pro': return '#5856d6'
    case 'Max': return '#ff9500'
    default: return '#8e8e93'
  }
})

const statusColor = computed(() => {
  switch (props.account.status) {
    case 'active': return '#34c759'
    case 'expired': return '#ff3b30'
    case 'suspended': return '#ff9500'
    default: return '#8e8e93'
  }
})

const statusText = computed(() => {
  switch (props.account.status) {
    case 'active': return '正常'
    case 'expired': return '已过期'
    case 'suspended': return '已暂停'
    default: return '未知'
  }
})

async function copyToClipboard(text: string, type: string) {
  try {
    await navigator.clipboard.writeText(text)
    emit('showToast', `${type}已复制到剪贴板`, 'success')
  } catch (err) {
    console.error('复制失败:', err)
    emit('showToast', '复制失败', 'error')
  }
}

function handleRefresh() {
  emit('refresh', props.account.id)
}

function handleEdit() {
  // 如果有原始邮箱，使用原始邮箱
  const accountToEdit = props.originalEmail 
    ? { ...props.account, email: props.originalEmail }
    : props.account
  emit('edit', accountToEdit)
}

function handleDelete() {
  // 直接触发删除事件,确认逻辑由父组件处理
  emit('delete', props.account.id)
}

// 处理卡片点击选择
function handleCardClick(event: MouseEvent) {
  // 如果点击的是按钮、输入框或其他交互元素，不触发选择
  const target = event.target as HTMLElement
  const isInteractive = target.closest('button, input, textarea, a, .action-btn, .login-btn, .test-login-btn, .copy-btn, .status-badge, .subscription-badge')
  
  if (!isInteractive) {
    // 阻止事件冒泡，避免触发其他点击事件
    event.stopPropagation()
    emit('toggleSelection', props.account.id)
  }
}

const loginLoading = ref(false)
const loginWindsurfLoading = ref(false)
const loginCursorLoading = ref(false)
const testLoginLoading = ref(false)

async function handleTestLogin() {
  try {
    testLoginLoading.value = true
    console.log('测试登录账户:', props.account.email)

    // 调用后端命令测试登录
    const result = await invoke<{ success: boolean; token?: string; account?: Account; error?: string }>('test_login_and_update', {
      accountId: props.account.id
    })

    if (result.success) {
      console.log('✅ 登录成功! Token 已更新')
      emit('showToast', '登录成功! Token 已更新', 'success')
      // 触发刷新以显示最新数据
      emit('refresh', props.account.id)
      // 设置为当前使用的账号
      emit('setCurrent', props.account.id)
    } else {
      console.error(`❌ 登录失败: ${result.error || '未知错误'}`)
      emit('showToast', `登录失败: ${result.error || '未知错误'}`, 'error')
    }
  } catch (error) {
    console.error('密码登录失败:', error)
    emit('showToast', `密码登录失败: ${error}`, 'error')
  } finally {
    testLoginLoading.value = false
  }
}

async function handleLogin() {
  if (!props.account.token) {
    console.error('该账户没有 Token,无法登录')
    return
  }

  try {
    loginLoading.value = true

    // 调用后端命令进行登录
    const result = await invoke<{ success: boolean; error?: string }>('login_to_vscode', {
      token: props.account.token
    })

    if (result.success) {
      console.log('✅ 已发送登录请求到 VS Code')
      emit('showToast', '已发送登录请求到 VS Code', 'success')
      // 设置为当前使用的账号
      emit('setCurrent', props.account.id)
    } else {
      console.error(`❌ 登录失败: ${result.error || '未知错误'}`)
      emit('showToast', `登录失败: ${result.error || '未知错误'}`, 'error')
    }
  } catch (error) {
    console.error('登录失败:', error)
    emit('showToast', `登录失败: ${error}`, 'error')
  } finally {
    loginLoading.value = false
  }
}

async function handleLoginWindsurf() {
  if (!props.account.token) {
    console.error('该账户没有 Token,无法登录')
    return
  }

  try {
    loginWindsurfLoading.value = true

    // 调用后端命令进行登录到 Windsurf
    const result = await invoke<{ success: boolean; error?: string }>('login_to_windsurf', {
      token: props.account.token
    })

    if (result.success) {
      console.log('✅ 已发送登录请求到 Windsurf')
      emit('showToast', '已发送登录请求到 Windsurf', 'success')
      // 设置为当前使用的账号
      emit('setCurrent', props.account.id)
    } else {
      console.error(`❌ 登录失败: ${result.error || '未知错误'}`)
      emit('showToast', `登录失败: ${result.error || '未知错误'}`, 'error')
    }
  } catch (error) {
    console.error('登录失败:', error)
    emit('showToast', `登录失败: ${error}`, 'error')
  } finally {
    loginWindsurfLoading.value = false
  }
}

async function handleLoginCursor() {
  if (!props.account.token) {
    console.error('该账户没有 Token,无法登录')
    return
  }

  try {
    loginCursorLoading.value = true

    // 调用后端命令进行登录到 Cursor
    const result = await invoke<{ success: boolean; error?: string }>('login_to_cursor', {
      token: props.account.token
    })

    if (result.success) {
      console.log('✅ 已发送登录请求到 Cursor')
      emit('showToast', '已发送登录请求到 Cursor', 'success')
      // 设置为当前使用的账号
      emit('setCurrent', props.account.id)
    } else {
      console.error(`❌ 登录失败: ${result.error || '未知错误'}`)
      emit('showToast', `登录失败: ${result.error || '未知错误'}`, 'error')
    }
  } catch (error) {
    console.error('登录失败:', error)
    emit('showToast', `登录失败: ${error}`, 'error')
  } finally {
    loginCursorLoading.value = false
  }
}
</script>

<template>
  <div
    class="account-card"
    :class="{ 
      selected: isSelected,
      current: isCurrent
    }"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @click="handleCardClick"
  >
    <div class="card-header">
      <div class="header-badges">
        <div class="status-badge" :style="{ backgroundColor: statusColor }">
          {{ statusText }}
        </div>
        <div class="subscription-badge" :style="{ backgroundColor: subscriptionColor }">
          {{ account.subscription_type || 'Free' }}
        </div>
      </div>
      <div class="card-actions">
        <button class="action-btn refresh-btn" @click="handleRefresh" title="刷新">
          <img src="/刷新.svg" alt="刷新" class="action-icon refresh-icon" />
        </button>
        <button class="action-btn edit-btn" @click="handleEdit" title="编辑">
          <img src="/编辑.svg" alt="编辑" class="action-icon" />
        </button>
        <button class="action-btn delete-btn" @click="handleDelete" title="删除">
          <img src="/删除 .svg" alt="删除" class="action-icon" />
        </button>
      </div>
    </div>

    <div class="card-body">
      <!-- 始终显示的关键信息 -->
      <div class="info-row">
        <span class="label">邮箱</span>
        <div class="value-with-copy">
          <span class="value email-text" :title="originalEmail || account.email">{{ account.email }}</span>
          <button 
            class="copy-btn" 
            @click="copyToClipboard(originalEmail || account.email, '邮箱')"
            title="复制邮箱"
          >
            <img src="/复制.svg" alt="复制" class="copy-icon" />
          </button>
        </div>
      </div>

      <div v-if="account.quota_remaining !== undefined" class="quota-section compact">
        <div class="quota-header">
          <span class="label">额度</span>
          <span class="quota-value">
            {{ account.quota_remaining }} / {{ account.quota_total }}
          </span>
        </div>
        <div class="quota-bar">
          <div
            class="quota-fill"
            :style="{ width: `${quotaPercentage}%` }"
          ></div>
        </div>
      </div>

      <div class="info-row no-border" v-if="account.current_period_end">
        <span class="label">订阅到期</span>
        <span class="value" :style="{ color: expireColor, fontWeight: '600' }">
          {{ subscriptionEndDate }}
        </span>
      </div>

      <!-- 悬停时显示的详细信息 -->
      <div class="expandable-content" :class="{ expanded: isHovered }">
        <div class="info-row">
          <span class="label">密码</span>
          <div class="value-with-copy">
            <span class="value">{{ showPassword ? account.password : '••••••••' }}</span>
            <button class="copy-btn" @click="showPassword = !showPassword">
              <img src="/显示.svg" alt="显示" class="copy-icon" :style="{ opacity: showPassword ? 1 : 0.6 }" />
            </button>
            <button class="copy-btn" @click="copyToClipboard(account.password, '密码')">
              <img src="/复制.svg" alt="复制" class="copy-icon" />
            </button>
          </div>
        </div>

        <div class="info-row">
          <span class="label">Token</span>
          <div class="value-with-copy">
            <span class="value">{{ account.token ? account.token.substring(0, 20) + '...' : '未获取' }}</span>
            <button
              v-if="account.token"
              class="copy-btn"
              @click="copyToClipboard(account.token!, 'Token')"
            >
              <img src="/复制.svg" alt="复制" class="copy-icon" />
            </button>
          </div>
        </div>

        <div class="info-row" v-if="account.token_expire_time">
          <span class="label">Token 过期</span>
          <span class="value">{{ tokenExpireDate }}</span>
        </div>

        <div class="info-row">
          <span class="label">注册时间</span>
          <span class="value">{{ registerDate }}</span>
        </div>
      </div>

      <!-- 操作按钮区域 -->
      <div class="action-buttons">
        <!-- VS Code 登录按钮 -->
        <button
          class="login-btn vscode-btn"
          @click="handleLogin"
          :disabled="!account.token || loginLoading"
          title="使用 Token 登录到 VS Code"
        >
          <img v-if="!loginLoading" src="/vscode.svg" alt="VS Code" class="btn-icon" />
          <span class="btn-text">{{ loginLoading ? '登录中' : 'VS Code' }}</span>
        </button>

        <!-- Windsurf 登录按钮 -->
        <button
          class="login-btn windsurf-btn"
          @click="handleLoginWindsurf"
          :disabled="!account.token || loginWindsurfLoading"
          title="使用 Token 登录到 Windsurf"
        >
          <img v-if="!loginWindsurfLoading" src="/windsurf.svg" alt="Windsurf" class="btn-icon" />
          <span class="btn-text">{{ loginWindsurfLoading ? '登录中' : 'Windsurf' }}</span>
        </button>

        <!-- Cursor 登录按钮 -->
        <button
          class="login-btn cursor-btn"
          @click="handleLoginCursor"
          :disabled="!account.token || loginCursorLoading"
          title="使用 Token 登录到 Cursor"
        >
          <img v-if="!loginCursorLoading" src="/cursor.svg" alt="Cursor" class="btn-icon" />
          <span class="btn-text">{{ loginCursorLoading ? '登录中' : 'Cursor' }}</span>
        </button>

        <!-- 密码登录按钮 -->
        <button
          class="test-login-btn"
          @click="handleTestLogin"
          :disabled="testLoginLoading"
          title="使用邮箱密码登录并更新 Token"
        >
          <img v-if="!testLoginLoading" src="/账密登录.svg" alt="密码登录" class="btn-icon" />
          <span class="btn-text">{{ testLoginLoading ? '登录中' : '密码登录' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.account-card {
  background: white;
  border-radius: 10px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  color: #1d1d1f;
  position: relative;
  border: 2px solid #e5e5e7;
  min-width: 0; /* 防止内容溢出网格 */
  max-width: 420px; /* 限制最大宽度，防止卡片过宽 */
  overflow: hidden; /* 防止内容溢出 */
  height: 100%; /* 让卡片高度自适应 */
  display: flex;
  flex-direction: column;
  cursor: pointer;
  user-select: none;
}

.account-card.selected {
  border-color: #34c759;
  background: linear-gradient(to bottom, #f8fff9, white);
  box-shadow: 0 2px 12px rgba(52, 199, 89, 0.15);
}

/* 当前使用账号的样式 */
.account-card.current {
  border-color: #ffc107;
  background: linear-gradient(to bottom, #fffef5, white);
  box-shadow: 0 2px 12px rgba(255, 193, 7, 0.2);
}

.account-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  z-index: 10;
  border-color: #007aff;
}

.account-card.selected:hover {
  box-shadow: 0 4px 16px rgba(52, 199, 89, 0.25);
  border-color: #34c759;
}

.account-card.current:hover {
  box-shadow: 0 4px 16px rgba(255, 193, 7, 0.3);
  border-color: #ffc107;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.header-badges {
  display: flex;
  gap: 6px;
  align-items: center;
}

.status-badge {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  background-color: #34c759;
  white-space: nowrap;
  color: white;
}

.card-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  background: #f5f5f7;
  border: none;
  border-radius: 6px;
  padding: 5px 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #e8e8ed;
}

.action-btn.delete:hover {
  background: #ffebeb;
}

.card-body {
  display: flex;
  flex-direction: column;
  flex: 1; /* 占用剩余空间 */
  min-width: 0; /* 防止内容溢出 */
}

/* 可展开内容区域 */
.expandable-content {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  margin-top: 0;
  transition: max-height 0.4s ease, opacity 0.3s ease, margin-top 0.3s ease;
}

.expandable-content.expanded {
  max-height: 500px;
  opacity: 1;
  margin-top: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid #f5f5f7;
  gap: 6px;
}

.info-row.no-border {
  border-bottom: none;
}

.info-row .label {
  flex-shrink: 0;
  min-width: 35px;
  font-size: 12px;
}

.label {
  font-size: 12px;
  color: #8e8e93;
  font-weight: 500;
}

.value {
  font-size: 13px;
  font-weight: 600;
  flex: 1;
  text-align: right;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  line-height: 18px;
}

.value.email-text {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  margin-right: 0;
  flex: 1 1 auto;
  min-width: 0;
}

.value-with-copy {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
  justify-content: flex-end;
  min-width: 0; /* 允许内容收缩 */
  max-width: 100%;
}

.value-with-copy .value {
  flex: 1 1 auto;
  text-align: right;
  padding-right: 2px;
  margin-right: 0;
}


.copy-btn {
  background: transparent;
  border: 1px solid #f0f0f0;
  border-radius: 3px;
  padding: 0;
  cursor: pointer;
  transition: all 0.2s;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  opacity: 0.6;
}

.copy-btn:hover {
  background: #f5f5f7;
  border-color: #007aff;
  opacity: 1;
}

.subscription-badge {
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  white-space: nowrap;
}

.expire-hint {
  font-size: 12px;
  margin-left: 4px;
  opacity: 0.9;
}

.quota-section {
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.quota-section.compact {
  padding: 6px 0;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.quota-value {
  font-size: 13px;
  font-weight: 600;
  text-align: right;
}

.quota-used {
  opacity: 0.8;
  font-size: 12px;
}

.quota-bar {
  height: 6px;
  background: #f5f5f7;
  border-radius: 3px;
  overflow: hidden;
}

.quota-fill {
  height: 100%;
  background: #34c759;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.quota-percentage {
  text-align: right;
  font-size: 11px;
  opacity: 0.8;
  margin-top: 4px;
}

.action-buttons {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e5e7;
  display: flex;
  gap: 6px;
}

.test-login-btn,
.login-btn {
  flex: 1;
  padding: 5px 6px;
  border: 1px solid #d2d2d7;
  border-radius: 6px;
  background: white;
  color: #1d1d1f;
  font-size: 10px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-height: 26px;
  position: relative;
}

.action-btn {
  background: white;
  border: 1px solid #e5e5e7;
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
}


.btn-icon {
  width: 14px;
  height: 14px;
  object-fit: contain;
  flex-shrink: 0;
}

.btn-text {
  font-size: 10px;
  line-height: 1;
}

.action-icon {
  width: 16px;
  height: 16px;
  object-fit: contain;
}

/* 刷新按钮旋转动画 */
@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.refresh-icon {
  transition: transform 0.3s ease;
}

.refresh-btn:hover .refresh-icon {
  animation: rotate 0.6s ease;
}

.copy-icon {
  width: 10px;
  height: 10px;
  object-fit: contain;
}

.test-login-btn:hover:not(:disabled) {
  background: #fff4e6;
  border-color: #ff9500;
}

.login-btn.vscode-btn:hover:not(:disabled) {
  background: #e5f2ff;
  border-color: #007aff;
}

.login-btn.windsurf-btn:hover:not(:disabled) {
  background: #f0efff;
  border-color: #5856d6;
}

.login-btn.cursor-btn:hover:not(:disabled) {
  background: #e8f5e8;
  border-color: #34c759;
}

/* 点击效果 */
.test-login-btn:active:not(:disabled),
.login-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.test-login-btn:disabled,
.login-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: #fafafa;
  border-color: #e5e5e7;
}

.test-login-btn:disabled .btn-icon,
.login-btn:disabled .btn-icon {
  opacity: 0.4;
}
</style>
