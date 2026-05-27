<template>
  <div class="chat-view">
    <ChatSidebar
      :sessions="sessions"
      :current-session="currentSession"
      @new-session="newSession"
      @select="selectSession"
      @delete="removeSession"
    />
    <div class="chat-main">
      <ChatWindow :messages="messages" :loading="loading" :status-msg="statusMsg" :current-session="currentSession" />
      <ChatInput :disabled="loading || !currentSession" @send="sendMessage" />
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatWindow  from '@/components/chat/ChatWindow.vue'
import ChatInput   from '@/components/chat/ChatInput.vue'
import { streamChat } from '@/api/chat'

export default {
  name: 'ChatView',
  components: { ChatSidebar, ChatWindow, ChatInput },
  data: () => ({ statusMsg: '' }),
  computed: {
    ...mapState('chat', ['sessions', 'currentSession', 'messages', 'loading'])
  },
  created() {
    this.loadSessions()
    this.loadTools()
  },
  methods: {
    ...mapActions('chat', ['loadSessions', 'newSession', 'selectSession', 'removeSession', 'loadTools']),

    async sendMessage({ message, mode }) {
      if (!this.currentSession) return

      this.$store.commit('chat/ADD_MESSAGE', { role: 'user', content: message })
      this.$store.commit('chat/SET_LOADING', true)
      this.$store.commit('chat/ADD_MESSAGE', { role: 'assistant', content: '' })
      this.statusMsg = ''
      let fullAnswer = ''

      streamChat(this.currentSession.id, message, mode, {
        onToken: (chunk) => {
            fullAnswer += chunk
            this.$store.commit('chat/UPDATE_LAST_MSG', fullAnswer)
        },
        onStatus: (msg) => {
            this.statusMsg = msg
        },
        // ← 추가: 재생성 시작 시 기존 답변 초기화
        onClear: () => {
            fullAnswer = ''
            this.$store.commit('chat/CLEAR_LAST_MSG')
            this.statusMsg = '🔄 답변을 다시 생성합니다...'
        },
        onDone: () => {
            this.$store.commit('chat/SET_LOADING', false)
            this.statusMsg = ''
            this.loadSessions()
        },
        onError: (err) => {
            this.$store.commit('chat/UPDATE_LAST_MSG', '오류: ' + err)
            this.$store.commit('chat/SET_LOADING', false)
            this.statusMsg = ''
        }
      })
    }
  }
}
</script>

<style scoped>
.chat-view { display: flex; height: 100%; overflow: hidden; }
.chat-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f4f6fb; }
</style>
