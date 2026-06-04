<template>
  <div class="sidebar">
    <!-- 기본지식 토글 -->
    <div class="knowledge-bar">
      <span class="knowledge-label">기본지식 사용</span>
      <label class="toggle">
        <input type="checkbox" v-model="localUseKnowledge" @change="onKnowledgeToggle" />
        <span class="toggle-slider" />
      </label>
    </div>
    <button class="new-chat-btn" @click="$emit('new-session')">새 채팅</button>
    <div class="session-list">

      <div
        v-for="s in sessions" :key="s.id"
        class="session-item"
        :class="{ active: currentSession && currentSession.id === s.id }"
        @click="$emit('select', s)"
      >
        <span class="session-title">{{ s.title || '새 채팅' }}</span>
        <span v-if="s.use_knowledge" class="k-badge">지식</span>
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
.sidebar { width: 260px; height: 100%; background: #ffffff; display: flex; flex-direction: column; padding: 16px 12px; gap: 12px; flex-shrink: 0; border-right: 1px solid #e2e8f0; }
.new-chat-btn { width: 100%; padding: 10px; background: #2563eb; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: background .15s ease; }
.new-chat-btn:hover { background: #1d4ed8; }
.session-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.session-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: 8px; cursor: pointer; color: #475569; font-size: 13.5px; transition: all .15s ease; }
.session-item:hover  { background: #f1f5f9; color: #0f172a; }
.session-item.active { background: rgba(37, 99, 235, 0.08); color: #2563eb; font-weight: 600; }
.session-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.k-badge {
  font-size: 10px; padding: 1px 5px; border: 1px solid #e2e8f0;
  border-radius: 4px; color: #64748b; background: #f8fafc;
  font-weight: 500; margin-left: 6px; flex-shrink: 0;
}
.del-btn { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 12px; padding: 2px 4px; border-radius: 4px; transition: color .15s; }
.del-btn:hover { color: #ef4444; }
.empty { color: #94a3b8; font-size: 13px; text-align: center; margin-top: 20px; }

.knowledge-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; margin-bottom: 4px;
  background: rgba(71, 85, 105, 0.04); border-radius: 8px; border: 1px solid rgba(71, 85, 105, 0.08);
}
.knowledge-label { font-size: 12px; color: #475569; font-weight: 500; }

/* 토글 스위치 (DocList와 동일) */
.toggle { position: relative; display: inline-block; width: 36px; height: 20px; cursor: pointer; }
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; inset: 0; background: #cbd5e1; border-radius: 20px; transition: background .2s; }
.toggle-slider:before { content: ""; position: absolute; width: 14px; height: 14px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: transform .2s; }
.toggle input:checked + .toggle-slider           { background: #2563eb; }
.toggle input:checked + .toggle-slider:before    { transform: translateX(16px); }
</style>
