<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { invoke } from '@tauri-apps/api/core'
import { getVersion } from '@tauri-apps/api/app'
import { open, confirm as tauriConfirm } from '@tauri-apps/plugin-dialog'
import AccountManager from './components/AccountManager.vue'
import Toast from './components/Toast.vue'

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

interface MachineGuidInfo {
  current_guid: string | null
  backup_guid: string | null
  has_backup: boolean
  platform: string
}

const activeTab = ref<'login' | 'reset' | 'accounts'>('accounts')
const debugSettings = ref('')  // 调试：配置文件内容
const token = ref('')
const deviceId = ref('python-auto-login')
const appVersion = ref('1.0.9')
const managerVersion = ref('1.3.0')  // 管理器版本（默认值）
const accountsStoragePath = ref('')  // 账号存储路径
const openVscode = ref(true)
const loading = ref(false)
const storageInfo = ref<StorageInfo | null>(null)
const showInfo = ref(false)
const generateNewDeviceId = ref(true)
const vscodeIds = ref<VSCodeIdsInfo | null>(null)
const showProxySettings = ref(false)
const proxyUrl = ref('')
const proxyEnabled = ref(false)

// 机器码管理相关状态
const machineGuidInfo = ref<MachineGuidInfo | null>(null)
const machineGuidLoading = ref(false)

// Verdent.exe 路径管理
const verdentExePath = ref<string | null>(null)

// Toast 相关状态
const showToast = ref(false)
const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info' | 'warning'>('success')

onMounted(async () => {
  await loadStorageInfo()
  await loadVSCodeIds()
  await loadProxySettings()
  await loadMachineGuidInfo()
  await loadVerdentExePath()
  
  // 检查管理员权限（仅Windows）
  try {
    const hasAdmin = await invoke<boolean>('check_admin_privileges')
    console.log('管理员权限状态:', hasAdmin)
    
    // 如果没有管理员权限，可以在这里提示用户
    if (!hasAdmin) {
      console.warn('应用未以管理员权限运行，某些功能可能受限')
      // 可选：显示一个提示信息
      // displayToast('提示：以管理员身份运行可获得完整功能', 'info')
    }
  } catch (error) {
    console.error('检查管理员权限失败:', error)
  }
  
  // 获取管理器版本号
  try {
    const version = await getVersion()
    managerVersion.value = version
  } catch (error) {
    console.error('获取版本号失败:', error)
    // 保持默认值 1.4.0
    managerVersion.value = '1.4.0'
  }
  
  // 获取账号存储路径
  try {
    const appDataPath = await invoke<string>('get_app_data_path')
    accountsStoragePath.value = appDataPath
  } catch (error) {
    accountsStoragePath.value = '获取失败'
  }
  
  // 禁用右键菜单
  document.addEventListener('contextmenu', handleContextMenu)
  
  // 禁用开发者工具快捷键
  document.addEventListener('keydown', handleKeydown)
  
  // 在生产环境中禁用控制台
  if (import.meta.env.PROD) {
    // 禁用控制台方法
    const noop = () => {}
    console.log = noop
    console.warn = noop
    console.error = noop
    console.info = noop
    console.debug = noop
    console.trace = noop
    console.table = noop
    console.group = noop
    console.groupEnd = noop
    console.groupCollapsed = noop
    console.clear = noop
    console.time = noop
    console.timeEnd = noop
    
    // 禁用 DevTools 检测
    const detectDevTools = () => {
      const threshold = 160
      if (window.outerWidth - window.innerWidth > threshold || 
          window.outerHeight - window.innerHeight > threshold) {
        // DevTools 可能已打开，可以选择刷新页面或显示警告
        document.body.innerHTML = '<h1 style="text-align:center;margin-top:50px;">请关闭开发者工具后刷新页面</h1>'
      }
    }
    
    // 定期检测
    setInterval(detectDevTools, 500)
  }
})

// 组件卸载时移除事件监听
onUnmounted(() => {
  document.removeEventListener('contextmenu', handleContextMenu)
  document.removeEventListener('keydown', handleKeydown)
})

// 处理右键事件
function handleContextMenu(e: MouseEvent) {
  e.preventDefault()
  return false
}

// 禁用开发者工具快捷键
function handleKeydown(e: KeyboardEvent) {
  // F12
  if (e.key === 'F12' || e.keyCode === 123) {
    e.preventDefault()
    return false
  }
  
  // Ctrl+Shift+I / Cmd+Option+I
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'I' || e.keyCode === 73)) {
    e.preventDefault()
    return false
  }
  
  // Ctrl+Shift+J / Cmd+Option+J
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'J' || e.keyCode === 74)) {
    e.preventDefault()
    return false
  }
  
  // Ctrl+Shift+C / Cmd+Option+C (元素检查)
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'C' || e.keyCode === 67)) {
    e.preventDefault()
    return false
  }
  
  // Ctrl+U / Cmd+U (查看源代码)
  if ((e.ctrlKey || e.metaKey) && (e.key === 'U' || e.key === 'u')) {
    e.preventDefault()
    return false
  }
}

async function loadStorageInfo() {
  try {
    storageInfo.value = await invoke<StorageInfo>('get_storage_info')
  } catch (error) {
    console.error('加载存储信息失败:', error)
  }
}

async function handleDebugSettings() {
  try {
    const settings = await invoke<string>('debug_print_settings')
    debugSettings.value = settings
    console.log('配置文件内容:', settings)
    showMessage('success', '配置文件内容已打印到控制台')
  } catch (error) {
    console.error('获取配置失败:', error)
    showMessage('error', `获取配置失败: ${error}`)
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

async function handleOpenFolder() {
  try {
    const path = await invoke('open_storage_folder')
    console.log('存储位置已打开:', path)
  } catch (error) {
    console.error('打开存储文件夹失败:', error)
    alert(`打开存储文件夹失败: ${error}`)
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
  // 只显示Toast消息
  toastMessage.value = text
  toastType.value = type === 'error' ? 'error' : type === 'info' ? 'info' : 'success'
  showToast.value = true
}

function handleToastClose() {
  showToast.value = false
}

async function loadProxySettings() {
  try {
    const settings = await invoke<{ enabled: boolean; url: string }>('get_proxy_settings')
    proxyEnabled.value = settings.enabled
    proxyUrl.value = settings.url
  } catch (error) {
    console.error('加载代理设置失败:', error)
  }
}

async function saveProxySettings() {
  try {
    await invoke('save_proxy_settings', {
      enabled: proxyEnabled.value,
      url: proxyUrl.value
    })
    showMessage('success', '代理设置已保存')
    showProxySettings.value = false
  } catch (error) {
    console.error('保存代理设置失败:', error)
    showMessage('error', '保存代理设置失败: ' + error)
  }
}

function handleProxyToggle() {
  // 当禁用代理时，可以清空代理地址
  if (!proxyEnabled.value) {
    // 可选：清空代理地址
    // proxyUrl.value = ''
  }
}

// 机器码管理函数
async function loadMachineGuidInfo() {
  try {
    machineGuidInfo.value = await invoke<MachineGuidInfo>('get_machine_guid_info')
  } catch (error) {
    console.error('加载机器码信息失败:', error)
  }
}

// Verdent.exe 路径管理函数
async function loadVerdentExePath() {
  try {
    verdentExePath.value = await invoke<string | null>('get_verdent_exe_path')
  } catch (error) {
    console.error('加载 Verdent.exe 路径失败:', error)
  }
}

async function selectVerdentExePath() {
  try {
    // 打开文件选择对话框
    const selected = await open({
      title: '选择 Verdent.exe 文件',
      filters: [{
        name: '可执行文件',
        extensions: ['exe']
      }]
    })
    
    if (!selected) {
      console.log('用户取消了选择')
      return
    }
    
    // 将选择的路径保存到设置
    const path = await invoke<string | null>('select_verdent_exe_path', {
      path: selected
    })
    
    if (path) {
      verdentExePath.value = path
      displayToast(`已设置 Verdent.exe 路径: ${path}`, 'success')
    }
  } catch (error) {
    console.error('选择 Verdent.exe 路径失败:', error)
    displayToast(`选择文件失败: ${error}`, 'error')
  }
}

async function clearVerdentExePath() {
  try {
    await invoke('clear_verdent_exe_path')
    verdentExePath.value = null
    displayToast('已清除 Verdent.exe 路径，将使用默认路径', 'success')
  } catch (error) {
    console.error('清除 Verdent.exe 路径失败:', error)
    displayToast(`清除路径失败: ${error}`, 'error')
  }
}

async function handleBackupMachineGuid() {
  const confirmed = await tauriConfirm(
    '备份后可以随时恢复到当前的机器码。',
    {
      title: '确认备份当前机器码?',
      kind: 'info'
    }
  )

  if (!confirmed) {
    return
  }

  machineGuidLoading.value = true
  try {
    const guid = await invoke<string>('backup_machine_guid')
    showMessage('success', `机器码已备份: ${guid}`)
    await loadMachineGuidInfo()
  } catch (error) {
    showMessage('error', `备份失败: ${error}`)
  } finally {
    machineGuidLoading.value = false
  }
}

async function handleResetMachineGuid() {
  // 步骤 1: 检查管理员权限
  try {
    const hasAdmin = await invoke<boolean>('check_admin_privileges')

    if (!hasAdmin) {
      // 权限不足，提示用户
      const shouldElevate = await tauriConfirm(
        '⚠️ 需要管理员权限\n\n' +
        '修改机器码需要写入系统注册表 (HKLM)，需要管理员权限。\n\n' +
        '是否以管理员身份重启应用？\n\n' +
        '注意：\n' +
        '• 重启后将保留所有账号数据\n' +
        '• 您需要在 UAC 提示中点击"是"',
        {
          title: '🔒 需要管理员权限',
          kind: 'warning'
        }
      )

      if (!shouldElevate) {
        showMessage('info', '已取消操作')
        return
      }

      // 请求权限提升
      try {
        showMessage('info', '正在请求管理员权限...')
        await invoke('request_admin_privileges')
        // 如果成功，应用会重启，不会执行到这里
      } catch (error) {
        showMessage('error', `权限提升失败: ${error}\n\n请手动以管理员身份运行应用`)
        return
      }
    }
  } catch (error) {
    console.error('检查权限失败:', error)
    showMessage('error', `检查权限失败: ${error}`)
    return
  }

  // 步骤 2: 确认操作
  const confirmed = await tauriConfirm(
    '此操作将:\n1. 生成新的随机机器码\n2. 写入系统注册表\n\n注意: 如果尚未备份,系统会自动备份当前机器码。\n\n是否继续?',
    {
      title: '⚠️ 重置机器码',
      kind: 'warning'
    }
  )

  if (!confirmed) {
    showMessage('info', '已取消重置操作')
    return
  }

  // 步骤 3: 执行重置
  machineGuidLoading.value = true
  try {
    const newGuid = await invoke<string>('reset_machine_guid')
    showMessage('success', `✓ 机器码已重置为: ${newGuid}`)
    await loadMachineGuidInfo()
  } catch (error) {
    showMessage('error', `重置失败: ${error}`)
  } finally {
    machineGuidLoading.value = false
  }
}

async function handleRestoreMachineGuid() {
  // 步骤 1: 检查管理员权限
  try {
    const hasAdmin = await invoke<boolean>('check_admin_privileges')

    if (!hasAdmin) {
      // 权限不足，提示用户
      const shouldElevate = await tauriConfirm(
        '⚠️ 需要管理员权限\n\n' +
        '恢复机器码需要写入系统注册表 (HKLM)，需要管理员权限。\n\n' +
        '是否以管理员身份重启应用？\n\n' +
        '注意：\n' +
        '• 重启后将保留所有账号数据\n' +
        '• 您需要在 UAC 提示中点击"是"',
        {
          title: '🔒 需要管理员权限',
          kind: 'warning'
        }
      )

      if (!shouldElevate) {
        showMessage('info', '已取消操作')
        return
      }

      // 请求权限提升
      try {
        showMessage('info', '正在请求管理员权限...')
        await invoke('request_admin_privileges')
        // 如果成功，应用会重启，不会执行到这里
      } catch (error) {
        showMessage('error', `权限提升失败: ${error}\n\n请手动以管理员身份运行应用`)
        return
      }
    }
  } catch (error) {
    console.error('检查权限失败:', error)
    showMessage('error', `检查权限失败: ${error}`)
    return
  }

  // 步骤 2: 确认操作
  const confirmed = await tauriConfirm(
    '这将把机器码恢复为首次备份时的原始值。',
    {
      title: '确认恢复到备份的机器码?',
      kind: 'warning'
    }
  )

  if (!confirmed) {
    showMessage('info', '已取消恢复操作')
    return
  }

  // 步骤 3: 执行恢复
  machineGuidLoading.value = true
  try {
    const guid = await invoke<string>('restore_machine_guid')
    showMessage('success', `✓ 机器码已恢复为: ${guid}`)
    await loadMachineGuidInfo()
  } catch (error) {
    showMessage('error', `恢复失败: ${error}`)
  } finally {
    machineGuidLoading.value = false
  }
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    showMessage('success', '已复制到剪贴板')
  } catch (error) {
    showMessage('error', '复制失败')
  }
}
</script>

<template>
  <div class="container">
    <!-- Toast 通知 -->
    <Toast
      :message="toastMessage"
      :type="toastType"
      :show="showToast"
      :duration="3000"
      @close="handleToastClose"
    />
    <div class="header">
      <h1>
        <img src="/verdent-long.svg" alt="Verdent" class="verdent-logo" />
        账号管理器
      </h1>
      <div class="header-actions">
        <button class="header-btn settings-btn" @click="showProxySettings = !showProxySettings" title="代理设置">
          <img src="/设置.svg" alt="设置" class="header-icon" />
        </button>
        <button class="header-btn info-btn" @click="showInfo = !showInfo" title="查看设备信息">
          <img src="/信息.svg" alt="信息" class="header-icon info-icon" />
        </button>
      </div>
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
            <div style="display: flex; align-items: center; gap: 8px;">
              <input :value="accountsStoragePath || '未知'" type="text" class="info-input" readonly style="flex: 1;" />
              <button 
                class="open-folder-btn" 
                @click="handleOpenFolder"
                title="打开存储文件夹"
              >
                <img src="/文件夹.svg" alt="" class="folder-icon" />
              </button>
            </div>
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
          <button class="btn-secondary" @click="loadVSCodeIds">
            <span style="display: inline-flex; align-items: center; gap: 6px;">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C14.8273 3 17.35 4.30367 19 6.34267" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M21 3V7H17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              刷新
            </span>
          </button>
          <button class="btn-primary" @click="showInfo = false">
            <span style="display: inline-flex; align-items: center; gap: 6px;">
              关闭
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 代理设置对话框 -->
    <div v-if="showProxySettings" class="modal-overlay" @click="showProxySettings = false">
      <div class="modal-content proxy-modal" @click.stop>
        <div class="modal-header">
          <h2>代理设置</h2>
          <button class="modal-close" @click="showProxySettings = false">
            <img src="/icon-close.svg" alt="关闭" class="close-icon" />
          </button>
        </div>
        <div class="modal-body">
          <div class="proxy-settings">
            <div class="proxy-item">
              <label class="proxy-label">
                <input type="checkbox" v-model="proxyEnabled" @change="handleProxyToggle" />
                <span>启用代理</span>
              </label>
            </div>
            <div class="proxy-item" v-if="proxyEnabled">
              <label class="proxy-label">代理地址</label>
              <input 
                v-model="proxyUrl" 
                type="text" 
                class="proxy-input" 
                placeholder="例如: http://127.0.0.1:7890 或 socks5://127.0.0.1:1080"
                :disabled="!proxyEnabled"
              />
              <div class="proxy-hint">支持 HTTP、HTTPS 和 SOCKS5 代理</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showProxySettings = false">取消</button>
          <button class="btn-primary" @click="saveProxySettings">保存</button>
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

        <!-- 机器码管理部分 -->
        <div class="machine-guid-container">
          <h3 class="section-title">
            <img src="/盾牌.svg" alt="盾牌" class="section-icon" width="20" height="20" />
            机器码管理
          </h3>

          <div v-if="machineGuidInfo?.platform === 'Windows'" class="machine-guid-section">
            <!-- 当前机器码卡片 -->
            <div class="guid-card primary-card">
              <div class="card-header">
                <div class="card-title">
                  <img src="/机器码.svg" alt="机器码" class="card-icon" width="16" height="16" />
                  <span>当前机器码</span>
                </div>
                <span class="card-badge">Windows 注册表 MachineGuid</span>
              </div>
              <div class="card-body">
                <div class="guid-display">
                  <input
                    :value="machineGuidInfo?.current_guid || '读取失败'"
                    type="text"
                    class="guid-input primary"
                    readonly
                  />
                  <button
                    v-if="machineGuidInfo?.current_guid"
                    class="copy-btn-modern"
                    @click="copyToClipboard(machineGuidInfo.current_guid)"
                    title="复制机器码"
                  >
                    <img src="/复制.svg" alt="复制" class="copy-icon" width="18" height="18" />
                  </button>
                </div>
              </div>
            </div>

            <!-- 备份机器码卡片（如果存在） -->
            <div v-if="machineGuidInfo?.has_backup" class="guid-card backup-card">
              <div class="card-header">
                <div class="card-title">
                  <img src="/备份.svg" alt="备份" class="card-icon" width="16" height="16" />
                  <span>备份机器码</span>
                </div>
                <span class="card-badge backup">首次备份的原始机器码</span>
              </div>
              <div class="card-body">
                <div class="guid-display">
                  <input
                    :value="machineGuidInfo?.backup_guid || '无'"
                    type="text"
                    class="guid-input backup"
                    readonly
                  />
                  <button
                    v-if="machineGuidInfo?.backup_guid"
                    class="copy-btn-modern"
                    @click="copyToClipboard(machineGuidInfo.backup_guid)"
                    title="复制备份机器码"
                  >
                    <img src="/复制.svg" alt="复制" class="copy-icon" width="18" height="18" />
                  </button>
                </div>
              </div>
            </div>

            <!-- 操作按钮区域 -->
            <div class="machine-guid-actions">
              <button
                v-if="!machineGuidInfo?.has_backup"
                class="action-button backup"
                @click="handleBackupMachineGuid"
                :disabled="machineGuidLoading"
              >
                <img src="/保存.svg" alt="备份" class="action-icon" width="16" height="16" />
                <span>备份当前机器码</span>
              </button>
              <button
                class="action-button reset"
                @click="handleResetMachineGuid"
                :disabled="machineGuidLoading"
              >
                <img src="/重置.svg" alt="重置" class="action-icon" width="16" height="16" />
                <span>重置机器码</span>
              </button>
              <button
                v-if="machineGuidInfo?.has_backup"
                class="action-button restore"
                @click="handleRestoreMachineGuid"
                :disabled="machineGuidLoading"
              >
                <img src="/恢复.svg" alt="恢复" class="action-icon" width="16" height="16" />
                <span>恢复备份</span>
              </button>
            </div>
            
            <!-- 警告提示 -->
            <div class="warning-notice">
              <img src="/警告.svg" alt="警告" class="warning-icon" width="16" height="16" />
              <span>修改机器码需要管理员权限。重置前会自动备份当前机器码。</span>
            </div>
          </div>
          <div v-else class="machine-guid-section">
            <div class="platform-not-supported">
              机器码管理功能仅支持 Windows 平台
            </div>
          </div>
        </div>

        <div class="divider"></div>

        <!-- Verdent.exe 路径管理 -->
        <div class="verdent-exe-section">
          <h3 class="section-title">
            <img src="/文件.svg" alt="文件" class="section-icon" width="20" height="20" />
            Verdent 客户端路径
          </h3>
          
          <div class="verdent-exe-content">
            <div class="path-info">
              <div class="path-label">当前路径:</div>
              <div class="path-value">
                {{ verdentExePath || '使用默认路径（自动检测）' }}
              </div>
            </div>
            
            <div class="path-actions">
              <button class="btn-secondary" @click="selectVerdentExePath">
                <img src="/文件夹.svg" alt="选择" class="btn-icon" width="16" height="16" />
                选择 Verdent.exe
              </button>
              <button 
                v-if="verdentExePath" 
                class="btn-secondary" 
                @click="clearVerdentExePath"
              >
                <img src="/删除 .svg" alt="清除" class="btn-icon" width="16" height="16" />
                清除路径
              </button>
            </div>
            
            <div class="path-hint">
              <img src="/信息.svg" alt="信息" class="hint-icon" width="14" height="14" />
              <span>如果 Verdent 客户端未安装在默认位置，请手动选择 Verdent.exe 文件</span>
            </div>
          </div>
        </div>

        <div class="divider"></div>

        <div v-if="storageInfo" class="storage-info">
          <h3>
            <img src="/存储.svg" alt="存储" class="section-icon" width="20" height="20" />
            存储信息
          </h3>
          <p><strong>存储路径:</strong> {{ storageInfo.path }}</p>
          <p><strong>存储项数量:</strong> {{ storageInfo.keys.length }}</p>

          <div v-if="storageInfo.keys.length > 0" class="storage-keys">
            <span v-for="key in storageInfo.keys" :key="key" class="storage-key">
              {{ key }}
            </span>
          </div>
          <p v-else style="margin-top: 12px; color: #999">暂无存储数据</p>
        </div>

        <div class="divider"></div>

        <div class="debug-section">
          <h3>
            <img src="/调试.svg" alt="调试" class="section-icon" width="20" height="20" />
            调试工具
          </h3>
          <button class="debug-btn" @click="handleDebugSettings">
            🔍 查看完整配置文件
          </button>
          <div v-if="debugSettings" class="debug-output">
            <pre>{{ debugSettings }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.debug-section {
  margin-top: 24px;
}

.debug-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.debug-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.debug-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.debug-btn:active {
  transform: translateY(0);
}

.debug-output {
  margin-top: 16px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  max-height: 400px;
  overflow-y: auto;
}

.debug-output pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
