<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  show: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmColor?: string
  type?: 'danger' | 'warning' | 'info'
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认操作',
  confirmText: '确认',
  cancelText: '取消',
  confirmColor: '#ef4444',
  type: 'warning'
})

const emit = defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    handleCancel()
  }
}

// 格式化消息,高亮警告文字
const formattedMessage = computed(() => {
  const lines = props.message.split('\n')
  return lines.map(line => {
    const trimmedLine = line.trim()
    // 检测警告文字模式
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
</script>

<template>
  <Transition name="modal">
    <div v-if="show" class="modal-overlay" @click="handleCancel" @keydown="handleKeydown" tabindex="0">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <div class="modal-icon" :class="`icon-${type}`">
            <span v-if="type === 'danger'">⚠️</span>
            <span v-else-if="type === 'warning'">⚠️</span>
            <span v-else>ℹ️</span>
          </div>
          <h3>{{ title }}</h3>
        </div>

        <div class="modal-body">
          <p v-for="(line, index) in formattedMessage" :key="index" :class="{ 'warning-text': line.isWarning }">
            {{ line.text }}
          </p>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="handleCancel">
            {{ cancelText }}
          </button>
          <button class="btn-confirm" @click="handleConfirm" :style="{ background: confirmColor }">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  min-width: 380px;
  max-width: 480px;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

.modal-header {
  padding: 20px 24px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-icon {
  font-size: 22px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  line-height: 1;
}

.modal-icon span {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.icon-danger {
  background: #fee2e2;
}

.icon-warning {
  background: #fef3c7;
}

.icon-info {
  background: #dbeafe;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  flex: 1;
}

.modal-body {
  padding: 0 24px 20px;
}

.modal-body p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #6b7280;
}

.modal-body p.warning-text {
  color: #ef4444;
  font-weight: 600;
  margin-top: 10px;
  padding: 8px 12px;
  background: #fef2f2;
  border-left: 3px solid #ef4444;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.modal-body p.warning-text::before {
  content: '⚠️';
  font-size: 14px;
  flex-shrink: 0;
}

.modal-footer {
  padding: 14px 24px;
  background: #f9fafb;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel,
.btn-confirm {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel {
  background: #e5e7eb;
  color: #374151;
}

.btn-cancel:hover {
  background: #d1d5db;
}

.btn-confirm {
  color: white;
}

.btn-confirm:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.9);
}

@keyframes modalSlideIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>

