<template>
  <div class="chat-window" ref="window">
    <div v-if="!currentSession" class="empty-guide">← 채팅을 선택하거나 새 채팅을 시작하세요</div>
    <template v-else>
      <MessageItem v-for="(m, i) in messages" :key="i" :msg="m" />
      <LoadingDots v-if="loading" :status="statusMsg" />
    </template>
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
.chat-window { flex: 1; overflow-y: auto; padding: 24px 20px; display: flex; flex-direction: column; }
.empty-guide { margin: auto; color: #aaa; font-size: 15px; }
</style>
