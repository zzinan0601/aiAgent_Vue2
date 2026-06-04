<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-popup">
      <!-- 헤더 -->
      <div class="modal-header">
        <div class="modal-title">
          <h3>현재 대화 컨텍스트</h3>
          <p class="modal-subtitle">로컬 LLM에 실제로 주입되는 최종 프롬프트 히스토리를 확인합니다.</p>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <!-- 바디 -->
      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <span>컨텍스트 데이터를 조회하고 있습니다...</span>
        </div>

        <div v-else-if="error" class="error-state">
          <span class="error-msg">⚠️ 오류가 발생했습니다: {{ error }}</span>
          <button class="retry-btn" @click="loadContext">다시 시도</button>
        </div>

        <template v-else>
          <div class="context-list">
            <div
              v-for="(msg, idx) in contextList"
              :key="idx"
              class="context-card"
              :class="msg.role"
            >
              <div class="card-header">
                <span class="role-badge" :class="msg.role">
                  {{ getRoleName(msg.role) }}
                </span>
                <span class="msg-index">#{{ idx + 1 }}</span>
              </div>

              <div class="card-body">
                <!-- 툴 결과 등 장황한 프롬프트는 스크롤 가능한 코드 블록으로 렌더링 -->
                <div v-if="isLongPrompt(msg.content)" class="long-prompt-wrap">
                  <div class="prompt-meta">
                    🛠️ 툴 결과가 결합된 최종 프롬프트 ({{ msg.content.length }}자)
                  </div>
                  <pre class="code-block"><code>{{ msg.content }}</code></pre>
                </div>
                <div v-else class="text-content">
                  {{ msg.content }}
                </div>
              </div>
            </div>

            <div v-if="!contextList.length" class="empty-state">
              조회할 컨텍스트 내역이 없습니다.
            </div>
          </div>
        </template>
      </div>

      <!-- 푸터 -->
      <div class="modal-footer">
        <button class="copy-btn" :disabled="loading || error" @click="copyToClipboard">
          {{ copied ? '✓ 복사 완료!' : '전체 복사하기' }}
        </button>
        <button class="close-action-btn" @click="$emit('close')">닫기</button>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchSessionContext } from '@/api/chat'

export default {
  name: 'SessionContextModal',
  props: {
    session: { type: Object, required: true }
  },
  data() {
    return {
      contextList: [],
      loading: true,
      error: null,
      copied: false
    }
  },
  created() {
    this.loadContext()
  },
  methods: {
    async loadContext() {
      this.loading = true
      this.error = null
      try {
        const data = await fetchSessionContext(this.session.id)
        this.contextList = data.context || []
      } catch (e) {
        this.error = e.response?.data?.detail || e.message || '알 수 없는 에러'
      } finally {
        this.loading = false
      }
    },
    getRoleName(role) {
      if (role === 'system') return 'System Prompt'
      if (role === 'user') return 'User Message'
      if (role === 'assistant') return 'Assistant Answer'
      return role
    },
    isLongPrompt(content) {
      // 툴 프롬프트 형식(문서 검색, DB 결과 지시어 등)이거나 길이가 180자 초과 시 코드블록 렌더링
      if (!content) return false
      return content.length > 180 || content.includes('다음은 사내 문서') || content.includes('다음은 DB 조회')
    },
    copyToClipboard() {
      if (this.copied) return
      
      let formattedText = `=== SESSION CONTEXT INFORMATION ===\n`
      formattedText += `Session ID: ${this.session.id}\n`
      formattedText += `Session Title: ${this.session.title || '새 채팅'}\n\n`

      this.contextList.forEach((msg, idx) => {
        const roleName = this.getRoleName(msg.role).toUpperCase()
        formattedText += `[#${idx + 1} - ${roleName}]\n`
        formattedText += `${msg.content}\n`
        formattedText += `-`.repeat(50) + `\n\n`
      })

      navigator.clipboard.writeText(formattedText)
        .then(() => {
          this.copied = true
          setTimeout(() => {
            this.copied = false
          }, 2000)
        })
        .catch(err => {
          alert('복사 실패: ' + err)
        })
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.3);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-popup {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  width: 760px; max-width: 94vw;
  max-height: 85vh;
  display: flex; flex-direction: column;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}
.modal-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}
.modal-header h3 {
  font-size: 16px; font-weight: 600; color: #0f172a; margin: 0;
}
.modal-subtitle {
  font-size: 12px; color: #64748b; margin: 4px 0 0 0;
}
.close-btn {
  background: #f1f5f9; border: none;
  width: 32px; height: 32px; border-radius: 50%;
  cursor: pointer; font-size: 14px; color: #64748b;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s ease;
}
.close-btn:hover {
  background: #e2e8f0; color: #0f172a;
}

.modal-body {
  flex: 1; overflow-y: auto;
  padding: 24px;
  background: #f8fafc;
}
.loading-state, .error-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 60px 0; gap: 16px;
}
.spinner {
  width: 32px; height: 32px;
  border: 3px solid rgba(37, 99, 235, 0.15);
  border-top-color: #2563eb; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loading-state span { font-size: 13.5px; color: #64748b; }
.error-msg { font-size: 13.5px; color: #ef4444; text-align: center; }
.retry-btn {
  padding: 6px 14px; background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 6px; font-size: 13px; color: #475569; cursor: pointer;
}
.retry-btn:hover { background: #f1f5f9; }

.context-list {
  display: flex; flex-direction: column; gap: 16px;
}
.context-card {
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 16px; display: flex; flex-direction: column; gap: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.01);
}

/* 시스템 프롬프트 카드 강조 */
.context-card.system {
  background: rgba(37, 99, 235, 0.04);
  border-color: rgba(37, 99, 235, 0.15);
}

.card-header {
  display: flex; align-items: center; justify-content: space-between;
}
.role-badge {
  font-size: 10.5px; font-weight: 700; padding: 2px 8px; border-radius: 20px;
}
.role-badge.system {
  background: rgba(37, 99, 235, 0.08); color: #2563eb;
}
.role-badge.user {
  background: rgba(71, 85, 105, 0.08); color: #475569;
}
.role-badge.assistant {
  background: rgba(16, 185, 129, 0.08); color: #10b981;
}
.msg-index {
  font-size: 11px; font-weight: 700; color: #94a3b8;
}

.card-body {
  font-size: 13.5px; line-height: 1.6; color: #334155;
  white-space: pre-wrap; word-break: break-all;
}
.text-content {
  font-family: inherit;
}

/* 긴 프롬프트(RAG 결과 등) 코드블록 렌더링 */
.long-prompt-wrap {
  display: flex; flex-direction: column; gap: 6px;
}
.prompt-meta {
  font-size: 11.5px; font-weight: 600; color: #2563eb;
  background: rgba(37, 99, 235, 0.05); padding: 4px 10px; border-radius: 6px;
  width: fit-content;
}
.code-block {
  margin: 0; background: #0f172a; color: #cbd5e1;
  padding: 14px; border-radius: 8px; font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 12.5px; max-height: 240px; overflow-y: auto;
  line-height: 1.5; text-align: left;
}
.code-block::-webkit-scrollbar {
  width: 6px;
}
.code-block::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15); border-radius: 4px;
}

.empty-state {
  text-align: center; color: #94a3b8; padding: 40px 0; font-size: 13.5px;
}

.modal-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 24px; border-top: 1px solid #e2e8f0;
  flex-shrink: 0; background: #f8fafc;
}
.copy-btn {
  padding: 8px 18px; background: #2563eb; border: none; border-radius: 8px;
  font-size: 13px; font-weight: 500; color: #ffffff; cursor: pointer;
  transition: background .15s;
}
.copy-btn:hover:not(:disabled) {
  background: #1d4ed8;
}
.copy-btn:disabled {
  background: #cbd5e1; color: #94a3b8; cursor: not-allowed;
}
.close-action-btn {
  padding: 8px 18px; background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 8px; font-size: 13px; font-weight: 500; color: #475569;
  cursor: pointer; transition: all .15s;
}
.close-action-btn:hover {
  background: #f1f5f9; color: #0f172a;
}
</style>
