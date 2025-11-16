# 警告文字高亮显示功能

## 功能概述

在自定义确认对话框 (`ConfirmDialog.vue`) 中,自动检测并高亮显示警告文字,提升用户对危险操作的警觉性。

## 实现方式

### 自动检测警告文字

系统会自动检测消息中包含以下关键词的行,并将其标记为警告文字:

- ✅ "不可撤销"
- ✅ "无法恢复"
- ✅ "永久删除"
- ✅ "谨慎操作"
- ✅ 以 "⚠" 开头的文字
- ✅ 以 "警告" 开头的文字
- ✅ 以 "注意" 开头的文字

### 视觉效果

**警告文字样式**:
- 🔴 **颜色**: `#ef4444` (红色)
- 💪 **字体粗细**: `600` (加粗)
- 📦 **背景**: `#fef2f2` (浅红色背景)
- 📏 **左边框**: `3px solid #ef4444` (红色边框)
- ⚠️ **图标**: 自动添加警告图标
- 📐 **间距**: 上方 12px 间距,内边距 8px 12px

**普通文字样式**:
- 🔘 **颜色**: `#6b7280` (灰色)
- 📝 **字体粗细**: 正常

## 使用示例

### 示例 1: 删除账户

**代码**:
```javascript
showConfirm(
  `确定要删除账户 "user@example.com" 吗?\n\n此操作不可撤销!`,
  async () => {
    await deleteAccount()
  },
  {
    title: '确认删除',
    confirmText: '删除',
    type: 'danger'
  }
)
```

**显示效果**:
```
确定要删除账户 "user@example.com" 吗?

⚠️ 此操作不可撤销!  (红色背景框,加粗显示)
```

### 示例 2: 重置操作

**代码**:
```javascript
showConfirm(
  `确定要重置所有设置吗?\n\n警告:所有自定义配置将永久删除!`,
  async () => {
    await resetSettings()
  },
  {
    title: '确认重置',
    confirmText: '重置',
    type: 'danger'
  }
)
```

**显示效果**:
```
确定要重置所有设置吗?

⚠️ 警告:所有自定义配置将永久删除!  (红色背景框,加粗显示)
```

### 示例 3: 多行警告

**代码**:
```javascript
showConfirm(
  `确定要执行此操作吗?\n\n注意:此操作将影响所有用户\n此操作不可撤销!`,
  async () => {
    await executeAction()
  }
)
```

**显示效果**:
```
确定要执行此操作吗?

⚠️ 注意:此操作将影响所有用户  (红色背景框)

⚠️ 此操作不可撤销!  (红色背景框)
```

## 技术实现

### 核心代码

**检测逻辑** (`ConfirmDialog.vue`):
```javascript
const formattedMessage = computed(() => {
  const lines = props.message.split('\n')
  return lines.map(line => {
    const trimmedLine = line.trim()
    const isWarning = 
      trimmedLine.includes('不可撤销') ||
      trimmedLine.includes('无法恢复') ||
      trimmedLine.includes('永久删除') ||
      trimmedLine.includes('谨慎操作') ||
      trimmedLine.startsWith('⚠') ||
      trimmedLine.startsWith('警告') ||
      trimmedLine.startsWith('注意')
    
    return {
      text: line,
      isWarning
    }
  })
})
```

**模板渲染**:
```vue
<div class="modal-body">
  <p v-for="(line, index) in formattedMessage" 
     :key="index" 
     :class="{ 'warning-text': line.isWarning }">
    {{ line.text }}
  </p>
</div>
```

**样式定义**:
```css
.modal-body p.warning-text {
  color: #ef4444;
  font-weight: 600;
  margin-top: 12px;
  padding: 8px 12px;
  background: #fef2f2;
  border-left: 3px solid #ef4444;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.modal-body p.warning-text::before {
  content: '⚠️';
  font-size: 16px;
  flex-shrink: 0;
}
```

## 优势

1. **🎯 自动化**: 无需手动添加样式,自动检测警告文字
2. **🎨 一致性**: 所有警告文字使用统一的视觉风格
3. **⚡ 高效**: 使用 Vue 计算属性,性能优秀
4. **🔧 可扩展**: 易于添加新的警告关键词
5. **🛡️ 安全性**: 有效防止用户误操作

## 测试验证

### 测试用例

1. **包含"不可撤销"的消息**
   - ✅ 应显示红色背景框
   - ✅ 应显示警告图标
   - ✅ 文字应加粗

2. **包含"警告"的消息**
   - ✅ 应显示红色背景框
   - ✅ 应显示警告图标

3. **普通消息**
   - ✅ 应显示灰色文字
   - ✅ 不应有背景框
   - ✅ 不应有警告图标

4. **多行混合消息**
   - ✅ 普通行显示灰色
   - ✅ 警告行显示红色背景框
   - ✅ 每个警告行都有独立的图标

## 后续优化建议

1. **可配置关键词**: 允许自定义警告关键词列表
2. **多级警告**: 支持不同级别的警告(警告/危险/致命)
3. **国际化**: 支持多语言警告关键词
4. **动画效果**: 为警告文字添加轻微的脉冲动画

## 总结

警告文字高亮功能通过自动检测和醒目的视觉设计,有效提升了用户对危险操作的警觉性,是一个重要的安全性改进。

