<template>
  <div class="sidebar">
    <!-- 기본지식 토글 -->
    <div class="knowledge-bar">
      <span class="knowledge-label">📚 기본지식 사용</span>
      <label class="toggle">
        <input type="checkbox" v-model="localUseKnowledge" @change="onKnowledgeToggle" />
        <span class="toggle-slider" />
      </label>
    </div>
    <button class="new-chat-btn" @click="$emit('new-session')">✏️ 새 채팅</button>
    <div class="session-list">

      <div
        v-for="s in sessions" :key="s.id"
        class="session-item"
        :class="{ active: currentSession && currentSession.id === s.id }"
        @click="$emit('select', s)"
      >
        <!-- 기본지식 세션 표시 -->
        <span v-if="s.system_prompt" class="knowledge-icon" title="기본지식 채팅">📚</span>
        
        <span class="session-title">{{ s.title || '새 채팅' }}</span>
        <button class="del-btn" @click.stop="$emit('delete', s.id)">✕</button>
      </div>
      <div v-if="!sessions.length" class="empty">채팅 내역 없음</div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
  name: 'ChatSidebar',
  props: {
    sessions       : { type: Array,  default: () => [] },
    currentSession : { type: Object, default: null     }
  },
  computed: {
    ...mapState('chat', ['useKnowledge']),
    localUseKnowledge: {
      get() { return this.useKnowledge },
      set(v) { this.$store.commit('chat/SET_USE_KNOWLEDGE', v) }
    }
  },
  methods: {
    onKnowledgeToggle() {
      // 토글 상태 변경 시 안내
    }
  }
}
</script>

<style scoped>
.sidebar { width: 240px; height: 100%; background: #1e2a3a; display: flex; flex-direction: column; padding: 12px 8px; gap: 8px; flex-shrink: 0; }
.new-chat-btn { width: 100%; padding: 10px; background: #3b82f6; color: #fff; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }
.new-chat-btn:hover { background: #2563eb; }
.session-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.session-item { display: flex; align-items: center; justify-content: space-between; padding: 9px 10px; border-radius: 8px; cursor: pointer; color: #b0c4de; font-size: 13px; }
.session-item:hover  { background: #2c3e55; }
.session-item.active { background: #2c3e55; color: #fff; }
.session-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.del-btn { background: none; border: none; color: #607080; cursor: pointer; font-size: 12px; padding: 2px 4px; border-radius: 4px; }
.del-btn:hover { color: #f87171; }
.empty { color: #607080; font-size: 13px; text-align: center; margin-top: 20px; }

.knowledge-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; margin-bottom: 4px;
  background: rgba(59,130,246,.1); border-radius: 8px;
}
.knowledge-label { font-size: 12px; color: #93c5fd; }
.knowledge-icon  { font-size: 11px; margin-right: 4px; flex-shrink: 0; }

/* 토글 스위치 (DocList와 동일) */
.toggle { position: relative; display: inline-block; width: 36px; height: 20px; cursor: pointer; }
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; inset: 0; background: #4a5568; border-radius: 20px; transition: background .2s; }
.toggle-slider:before { content: ""; position: absolute; width: 14px; height: 14px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: transform .2s; }
.toggle input:checked + .toggle-slider           { background: #3b82f6; }
.toggle input:checked + .toggle-slider:before    { transform: translateX(16px); }
</style>
