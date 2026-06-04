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
      <ChatWindow
        :messages="messages"
        :loading="loading"
        :status-msg="statusMsg"
        :current-session="currentSession"
        @open-settings="showSettings = true"
        @open-context="showContext = true"
      />
      <ChatInput :disabled="loading || !currentSession" @send="sendMessage" />
    </div>

    <!-- 세션 설정 모달 -->
    <SessionSettingsModal
      v-if="showSettings && currentSession"
      :session="currentSession"
      @close="showSettings = false"
      @saved="onSettingsSaved"
    />
    <!-- 컨텍스트 보기 모달 -->
    <SessionContextModal
      v-if="showContext && currentSession"
      :session="currentSession"
      @close="showContext = false"
    />
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatWindow  from '@/components/chat/ChatWindow.vue'
import ChatInput   from '@/components/chat/ChatInput.vue'
import SessionSettingsModal from '@/components/chat/SessionSettingsModal.vue'
import SessionContextModal from '@/components/chat/SessionContextModal.vue'
import { streamChat } from '@/api/chat'

export default {
  name: 'ChatView',
  components: { ChatSidebar, ChatWindow, ChatInput, SessionSettingsModal, SessionContextModal },
  data: () => ({ statusMsg: '', showSettings: false, showContext: false }),
  computed: {
    ...mapState('chat', ['sessions', 'currentSession', 'messages', 'loading'])
  },
  created() {
    this.loadSessions()
    this.loadTools()
  },
  methods: {
    ...mapActions('chat', ['loadSessions', 'newSession', 'selectSession', 'removeSession', 'loadTools']),

    onSettingsSaved() {
      if (this.currentSession) {
        this.selectSession(this.currentSession) // 세션 변경사항 반영을 위해 재로드
      }
    },

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
.chat-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: #f8fafc; }
</style>
