<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import AccountManager from './components/AccountManager.vue'

interface LoginRequest {
  token: string
  device_id?: string
  app_version?: string
}

interface LoginResponse {
  success: boolean
  access_token?: string
  error?: string
  callback_url?: string
}

interface ResetResponse {
  success: boolean
  deleted_count: number
  deleted_keys: string[]
  error?: string
}

interface StorageInfo {
  path: string
  keys: string[]
}

interface VSCodeIdsInfo {
  success: boolean
  storage_path: string
  sqm_id: string | null
  device_id: string | null
  machine_id: string | null
  extension_version: string | null
  error: string | null
}

const activeTab = ref<'login' | 'reset' | 'accounts'>('accounts')
const token = ref('')
const deviceId = ref('python-auto-login')
const appVersion = ref('1.0.9')
const managerVersion = ref('1.0.0')  // 管理器版本
const accountsStoragePath = ref('')  // 账号存储路径
const openVscode = ref(true)
const loading = ref(false)
const message = ref<{ type: 'success' | 'error' | 'info'; text: string } | null>(null)
const storageInfo = ref<StorageInfo | null>(null)
const showInfo = ref(false)
const generateNewDeviceId = ref(true)
const vscodeIds = ref<VSCodeIdsInfo | null>(null)

onMounted(async () => {
  await loadStorageInfo()
  await loadVSCodeIds()
  // 获取账号存储路径
  try {
    const appDataPath = await invoke<string>('get_app_data_path')
    accountsStoragePath.value = appDataPath
  } catch (error) {
    accountsStoragePath.value = '获取失败'
  }
})

async function loadStorageInfo() {
  try {
    storageInfo.value = await invoke<StorageInfo>('get_storage_info')
  } catch (error) {
    console.error('加载存储信息失败:', error)
  }
}

async function loadVSCodeIds() {
  try {
    vscodeIds.value = await invoke<VSCodeIdsInfo>('get_vscode_ids')
    if (vscodeIds.value.success && vscodeIds.value.extension_version) {
      appVersion.value = vscodeIds.value.extension_version
    }
  } catch (error) {
    console.error('加载VS Code IDs失败:', error)
  }
}

async function handleLogin() {
  if (!token.value.trim()) {
    showMessage('error', '请输入Token')
    return
  }

  loading.value = true
  message.value = null

  try {
    const request: LoginRequest = {
      token: token.value.trim(),
      device_id: deviceId.value || undefined,
      app_version: appVersion.value || undefined,
    }

    const response = await invoke<LoginResponse>('login_with_token', { request })

    if (response.success) {
      showMessage('success', `登录成功! 访问令牌: ${response.access_token?.substring(0, 20)}...`)
      
      if (openVscode.value && response.callback_url) {
        try {
          await invoke('open_vscode_callback', { callbackUrl: response.callback_url })
          showMessage('info', 'VS Code回调链接已打开')
        } catch (error) {
          console.error('打开VS Code失败:', error)
        }
      }

      await loadStorageInfo()
    } else {
      showMessage('error', response.error || '登录失败')
    }
  } catch (error: any) {
    showMessage('error', `登录失败: ${error}`)
  } finally {
    loading.value = false
  }
}

async function handleResetDevice() {
  if (!confirm('🔄 重置设备身份标识 - 清理多账号检测相关数据\n\n此操作将:\n1. 删除所有账户认证信息\n2. 清除用户信息缓存\n3. 重置设备标识(可选)\n4. 清除任务历史记录\n\n这将使系统恢复到"全新设备首次登录"状态。\n\n是否继续?')) {
    return
  }

  loading.value = true
  message.value = null

  try {
    const response = await invoke<ResetResponse>('reset_device_identity', {
      generateNewDeviceId: generateNewDeviceId.value
    })

    if (response.success) {
      let msg = `✅ 设备身份已重置!\n\n清除了 ${response.deleted_count} 个存储项:`
      if (response.deleted_keys.length > 0) {
        msg += '\n' + response.deleted_keys.map(k => `• ${k}`).join('\n')
      }
      msg += '\n\n💡 提示:\n- 所有账户关联信息已清除\n- 系统状态已恢复到"全新设备首次登录"\n- 现在可以使用新账号登录而不会被检测到多账号关联'
      
      alert(msg)
      await loadStorageInfo()
      await loadVSCodeIds()
    } else {
      showMessage('error', response.error || '重置失败')
    }
  } catch (error: any) {
    showMessage('error', `重置失败: ${error}`)
  } finally {
    loading.value = false
  }
}

async function handleResetAll() {
  const storageKeys = [
    'secrets_ycAuthToken',
    'secrets_verdentApiKey',
    'secrets_authNonce',
    'secrets_authNonceTimestamp',
    'globalState_userInfo',
    'globalState_apiProvider',
    'globalState_taskHistory',
    'workspaceState_isPlanMode',
    'workspaceState_thinkLevel',
    'workspaceState_selectModel'
  ]
  
  let confirmMsg = '⚠️ 警告: 完全清理模式\n\n'
  confirmMsg += '此操作将删除所有 Verdent AI 扩展的本地存储数据，包括:\n'
  confirmMsg += '• 所有认证信息 (tokens, API keys)\n'
  confirmMsg += '• 所有用户信息 (账户、订阅状态)\n'
  confirmMsg += '• 所有配置信息 (API 提供商、任务历史)\n'
  confirmMsg += '• 所有用户偏好 (计划模式、思考级别、模型选择)\n\n'
  confirmMsg += `将要删除的存储项 (共 ${storageKeys.length} 项):\n`
  storageKeys.forEach((key, i) => {
    confirmMsg += `${i + 1}. ${key}\n`
  })
  confirmMsg += '\n确定要继续吗?'
  
  if (!confirm(confirmMsg)) {
    return
  }

  const confirmText = prompt('⚠️ 确认要删除所有数据吗? (输入 "YES" 确认):')
  if (confirmText !== 'YES') {
    showMessage('info', '❌ 操作已取消')
    return
  }

  loading.value = true
  message.value = null

  try {
    const response = await invoke<ResetResponse>('reset_all_storage', {
      generateNewDeviceId: generateNewDeviceId.value
    })

    if (response.success) {
      let msg = `✅ 完全清理完成!\n\n删除了 ${response.deleted_count} 个存储项:`
      if (response.deleted_keys.length > 0) {
        msg += '\n' + response.deleted_keys.map(k => `• ${k}`).join('\n')
      }
      msg += '\n\n💡 提示:\n- 所有 Verdent AI 扩展数据已清除\n- 本地存储已恢复到"从未安装"状态\n- 所有用户偏好设置已重置\n- 现在可以重新配置或使用新账号登录'
      
      alert(msg)
      await loadStorageInfo()
      await loadVSCodeIds()
    } else {
      showMessage('error', response.error || '清除失败')
    }
  } catch (error: any) {
    showMessage('error', `清除失败: ${error}`)
  } finally {
    loading.value = false
  }
}

function showMessage(type: 'success' | 'error' | 'info', text: string) {
  message.value = { type, text }
  setTimeout(() => {
    message.value = null
  }, 5000)
}
</script>

<template>
  <div class="container">
    <div class="header">
      <h1>
        <img src="/verdent-long.svg" alt="Verdent" class="verdent-logo" />
        账号管理器
      </h1>
      <button class="info-btn" @click="showInfo = !showInfo" title="查看设备信息">
        <img src="/信息.svg" alt="信息" class="info-icon" />
      </button>
    </div>

    <div v-if="showInfo" class="modal-overlay" @click="showInfo = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>设备信息</h2>
          <button class="modal-close info-modal-close" @click="showInfo = false">
            <img src="/icon-close.svg" alt="关闭" class="close-icon" />
          </button>
        </div>
        <div class="modal-body">
          <div class="info-item">
            <div class="info-label">管理器版本</div>
            <input :value="managerVersion" type="text" class="info-input" readonly />
            <div class="info-hint">Verdent账号管理器软件版本</div>
          </div>
          <div class="info-item">
            <div class="info-label">扩展版本</div>
            <input :value="appVersion" type="text" class="info-input" readonly />
            <div class="info-hint">从VS Code扩展目录自动读取</div>
          </div>
          <div class="info-item">
            <div class="info-label">账号存储位置</div>
            <input :value="accountsStoragePath || '未知'" type="text" class="info-input" readonly />
            <div class="info-hint">账号数据文件存储路径</div>
          </div>
          <div class="info-item">
            <div class="info-label">VS Code - sqmId</div>
            <input :value="vscodeIds?.sqm_id || '未读取'" type="text" class="info-input" readonly />
            <div class="info-hint">VS Code遥测ID（UUID格式）</div>
          </div>
          <div class="info-item">
            <div class="info-label">VS Code - devDeviceId</div>
            <input :value="vscodeIds?.device_id || '未读取'" type="text" class="info-input" readonly />
            <div class="info-hint">VS Code设备ID（UUID格式）</div>
          </div>
          <div class="info-item">
            <div class="info-label">VS Code - machineId</div>
            <input :value="vscodeIds?.machine_id || '未读取'" type="text" class="info-input" readonly />
            <div class="info-hint">VS Code机器ID（SHA256哈希）</div>
          </div>
          <div class="info-item">
            <div class="info-label">VS Code 存储路径</div>
            <input :value="vscodeIds?.storage_path || '未知'" type="text" class="info-input" readonly />
            <div class="info-hint">storage.json文件位置</div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="loadVSCodeIds">刷新</button>
          <button class="btn-primary" @click="showInfo = false">关闭</button>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="tabs">
        <button
          :class="['tab', { active: activeTab === 'accounts' }]"
          @click="activeTab = 'accounts'"
        >
          账户管理
        </button>
        <button
          :class="['tab', { active: activeTab === 'login' }]"
          @click="activeTab = 'login'"
        >
          登录管理
        </button>
        <button
          :class="['tab', { active: activeTab === 'reset' }]"
          @click="activeTab = 'reset'"
        >
          存储管理
        </button>
      </div>

      <div v-if="message" :class="['alert', `alert-${message.type}`]">
        {{ message.text }}
      </div>

      <div v-if="activeTab === 'accounts'">
        <AccountManager />
      </div>

      <div v-else-if="activeTab === 'login'">
        <div class="form-group">
          <label for="token">Token *</label>
          <textarea
            id="token"
            v-model="token"
            placeholder="请粘贴你的Verdent AI Token (例如: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...)"
          />
          <p class="help-text">从浏览器Cookie中获取的token值</p>
        </div>

        <div class="form-group checkbox-group">
          <input id="openVscode" v-model="openVscode" type="checkbox" />
          <label for="openVscode">登录后自动打开VS Code回调链接</label>
        </div>

        <div class="button-group">
          <button class="btn-primary" :disabled="loading" @click="handleLogin">
            <span v-if="loading" class="loading"></span>
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </div>
      </div>

      <div v-else-if="activeTab === 'reset'">
        <div class="alert alert-info">
          <strong>提示:</strong>
          <ul style="margin-top: 8px; margin-left: 20px">
            <li><strong>重置设备身份:</strong> 仅清理账户相关数据，保留用户偏好设置</li>
            <li><strong>完全清理:</strong> 清理所有数据，包括用户偏好、工作区配置等</li>
            <li>切换账号前建议使用"重置设备身份"避免多账号检测</li>
          </ul>
        </div>

        <div class="form-group checkbox-group">
          <input id="generateNewDeviceId" v-model="generateNewDeviceId" type="checkbox" />
          <label for="generateNewDeviceId">清理时生成新的设备ID</label>
        </div>

        <div class="button-group">
          <button class="btn-secondary" :disabled="loading" @click="handleResetDevice">
            <span v-if="loading" class="loading"></span>
            重置设备身份
          </button>
          <button class="btn-danger" :disabled="loading" @click="handleResetAll">
            <span v-if="loading" class="loading"></span>
            完全清理
          </button>
        </div>

        <div class="divider"></div>

        <div v-if="storageInfo" class="storage-info">
          <h3>📦 存储信息</h3>
          <p><strong>存储路径:</strong> {{ storageInfo.path }}</p>
          <p><strong>存储项数量:</strong> {{ storageInfo.keys.length }}</p>
          
          <div v-if="storageInfo.keys.length > 0" class="storage-keys">
            <span v-for="key in storageInfo.keys" :key="key" class="storage-key">
              {{ key }}
            </span>
          </div>
          <p v-else style="margin-top: 12px; color: #999">暂无存储数据</p>
        </div>
      </div>
    </div>
  </div>
</template>
