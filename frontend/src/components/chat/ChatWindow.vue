<template>
  <div class="chat-window-wrap">
    <!-- 세션 정보 헤더 추가 -->
    <div v-if="currentSession" class="chat-header">
      <div class="chat-header-title">
        <span class="title-text">{{ currentSession.title || '새 채팅' }}</span>
      </div>
      <div class="chat-header-actions">
        <button class="settings-trigger-btn context-btn" @click="$emit('open-context')">
          컨텍스트 보기
        </button>
        <button class="settings-trigger-btn" @click="$emit('open-settings')">
          설정
        </button>
      </div>
    </div>

    <div class="chat-window" ref="window">
      <div v-if="!currentSession" class="empty-guide">채팅을 선택하거나 새 채팅을 시작하세요.</div>
      <template v-else>
        <MessageItem v-for="(m, i) in messages" :key="i" :msg="m" />
        <LoadingDots v-if="loading" :status="statusMsg" />
      </template>
    </div>
  </div>
</template>

<script>
import MessageItem from './MessageItem.vue'
import LoadingDots from './LoadingDots.vue'

export default {
  name: 'ChatWindow',
  components: { MessageItem, LoadingDots },
  props: {
    messages      : { type: Array,   default: () => [] },
    loading       : { type: Boolean, default: false    },
    statusMsg     : { type: String,  default: ''       },
    currentSession: { type: Object,  default: null     }
  },
  watch: {
    messages() { this.$nextTick(this.scrollBottom) },
    loading()  { this.$nextTick(this.scrollBottom) }
  },
  methods: {
    scrollBottom() {
      const el = this.$refs.window
      if (el) el.scrollTop = el.scrollHeight
    }
  }
}
</script>

<style scoped>
.chat-window-wrap { display: flex; flex-direction: column; flex: 1; overflow: hidden; height: 100%; }
.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px; border-bottom: 1px solid #e2e8f0;
  background: #ffffff; flex-shrink: 0; min-height: 52px;
}
.chat-header-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 14.5px; font-weight: 600; color: #0f172a;
}
.title-text {
  max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.chat-header-actions {
  display: flex;
  gap: 8px;
}
.settings-trigger-btn {
  padding: 6px 14px; background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 8px; font-size: 12.5px; font-weight: 500; color: #475569;
  cursor: pointer; transition: all .15s ease;
}
.settings-trigger-btn:hover {
  background: rgba(71, 85, 105, 0.05); border-color: rgba(71, 85, 105, 0.2);
  color: #334155;
}
.context-btn {
  border-color: rgba(37, 99, 235, 0.2);
  color: #2563eb;
}
.context-btn:hover {
  background: rgba(37, 99, 235, 0.05);
  border-color: rgba(37, 99, 235, 0.4);
  color: #1d4ed8;
}
.chat-window { flex: 1; overflow-y: auto; padding: 24px 20px; display: flex; flex-direction: column; }
.empty-guide { margin: auto; color: #94a3b8; font-size: 14px; }
</style>
