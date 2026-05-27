<template>
  <div class="doc-list">
    <h3>📋 업로드된 문서</h3>
    <div v-if="!documents.length" class="empty">업로드된 문서가 없습니다.</div>
    <table v-else class="table">
      <thead>
        <tr><th>파일명</th><th>청크 수</th><th>기본지식</th><th>상태</th><th>등록일</th><th>삭제</th></tr>
      </thead>
      <tbody>
        <tr v-for="doc in documents" :key="doc.id">
          <td>{{ doc.filename }}</td>
          <td>
            <span class="chunk-btn" :class="{ disabled: doc.status !== 'done' }" @click="doc.status === 'done' && openChunks(doc.id)">
              {{ doc.chunk_count }}
            </span>
          </td>
          <!-- 기본지식 체크박스 -->
          <td class="knowledge-cell">
            <label class="toggle" :title="doc.status !== 'done' ? '임베딩 완료 후 설정 가능' : ''">
              <input
                type="checkbox"
                :checked="doc.is_knowledge"
                :disabled="doc.status !== 'done'"
                @change="onKnowledgeChange(doc, $event)"
              />
              <span class="toggle-slider" />
            </label>
          </td>
          <td><span class="badge" :class="doc.status">{{ statusLabel(doc.status) }}</span></td>
          <td>{{ formatDate(doc.created_at) }}</td>
          <td><button class="del-btn" @click="$emit('delete', doc.id)">🗑️</button></td>
        </tr>
      </tbody>
    </table>

    <!-- 청크 팝업 -->
    <div v-if="popup.show" class="overlay" @click.self="closePopup">
      <div class="popup">
        <div class="popup-header">
          <div class="popup-title">
            <span class="popup-icon">📄</span>
            <div>
              <div class="popup-filename">{{ popup.filename }}</div>
              <div class="popup-sub">총 {{ popup.chunks.length }}개 청크</div>
            </div>
          </div>
          <div class="header-actions">
            <button class="expand-all-btn" @click="toggleAll">{{ allExpanded ? '전체 접기 ▲' : '전체 펼치기 ▼' }}</button>
            <button class="close-btn" @click="closePopup">✕</button>
          </div>
        </div>
        <div class="popup-search">
          <input v-model="popup.search" placeholder="청크 내용 검색..." class="search-input" @input="onSearch" />
          <span class="search-count">{{ filteredChunks.length }} / {{ popup.chunks.length }}</span>
        </div>
        <div class="popup-body">
          <div v-if="popup.loading" class="popup-loading">⏳ 불러오는 중...</div>
          <div v-else-if="!filteredChunks.length" class="popup-empty">검색 결과가 없습니다.</div>
          <div v-else v-for="chunk in filteredChunks" :key="chunk.index" class="chunk-item" :class="{ open: expandedSet[chunk.index] }">
            <div class="chunk-header" @click="toggle(chunk.index)">
              <div class="chunk-left">
                <span class="chunk-arrow">{{ expandedSet[chunk.index] ? '▼' : '▶' }}</span>
                <span class="chunk-index"># {{ chunk.index + 1 }}</span>
                <span v-if="!expandedSet[chunk.index]" class="chunk-preview">{{ chunk.text.slice(0, 60) }}{{ chunk.text.length > 60 ? '...' : '' }}</span>
              </div>
              <span class="chunk-len">{{ chunk.text.length }}자</span>
            </div>
            <transition name="slide">
              <div v-if="expandedSet[chunk.index]" class="chunk-text" v-html="highlight(chunk.text)" />
            </transition>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchChunks, toggleKnowledge } from '@/api/rag'

export default {
  name: 'DocList',
  props: { documents: { type: Array, default: () => [] } },
  data: () => ({
    popup      : { show: false, loading: false, filename: '', chunks: [], search: '' },
    expandedSet: {}
  }),
  computed: {
    filteredChunks() {
      const q = this.popup.search.trim().toLowerCase()
      if (!q) return this.popup.chunks
      return this.popup.chunks.filter(c => c.text.toLowerCase().includes(q))
    },
    allExpanded() { return this.filteredChunks.every(c => this.expandedSet[c.index]) }
  },
  methods: {
    // ── 기본지식 토글 ──
    async onKnowledgeChange(doc, event) {
      const checked = event.target.checked
      try {
        await toggleKnowledge(doc.id, checked)
        doc.is_knowledge = checked
        const msg = checked
          ? doc.filename + " 을(를) 기본지식으로 설정했습니다."
          : doc.filename + " 기본지식을 해제했습니다."
        alert(msg)
      } catch (e) {
        event.target.checked = !checked   // 롤백
        alert("설정 실패: " + (e.response?.data?.detail || e.message))
      }
    },
    async openChunks(docId) {
      this.popup.show    = true
      this.popup.loading = true
      this.popup.chunks  = []
      this.popup.search  = ''
      this.expandedSet   = {}
      try {
        const data          = await fetchChunks(docId)
        this.popup.filename = data.filename
        this.popup.chunks   = data.chunks
      } catch {
        this.popup.chunks = [{ index: 0, text: '청크 데이터를 불러오지 못했습니다.' }]
      } finally {
        this.popup.loading = false
      }
    },
    closePopup() { this.popup.show = false; this.popup.search = ''; this.expandedSet = {} },
    toggle(index) { this.$set(this.expandedSet, index, !this.expandedSet[index]) },
    toggleAll() {
      const next = !this.allExpanded
      const updated = {}
      this.filteredChunks.forEach(c => { updated[c.index] = next })
      this.expandedSet = updated
    },
    onSearch() {
      const q = this.popup.search.trim().toLowerCase()
      if (!q) return
      const updated = Object.assign({}, this.expandedSet)
      this.popup.chunks.forEach(c => { if (c.text.toLowerCase().includes(q)) updated[c.index] = true })
      this.expandedSet = updated
    },
    highlight(text) {
      const q = this.popup.search.trim()
      if (!q) return this.escapeHtml(text)
      const escaped = this.escapeHtml(text)
      const re = new RegExp('(' + this.escapeRegex(q) + ')', 'gi')
      return escaped.replace(re, '<mark>$1</mark>')
    },
    escapeHtml(str) { return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') },
    escapeRegex(str) { return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') },
    statusLabel(s) { return { pending: '⏳ 임베딩중', done: '✅ 완료', error: '❌ 오류' }[s] || s },
    formatDate(dt) { return new Date(dt).toLocaleDateString('ko-KR') }
  }
}
</script>

<style scoped>
.doc-list { background: #fff; border-radius: 12px; padding: 24px; }
h3 { margin-bottom: 16px; }
.empty { color: #aaa; font-size: 14px; }
.table { width: 100%; border-collapse: collapse; font-size: 14px; }
.table th { background: #f8fafc; padding: 10px 14px; text-align: left; border-bottom: 2px solid #e2e8f0; }
.table td { padding: 10px 14px; border-bottom: 1px solid #f0f4f8; }
.table tr:hover td { background: #f8fafc; }
.chunk-btn { display: inline-block; padding: 3px 10px; background: #eff6ff; color: #2563eb; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; }
.chunk-btn:hover { background: #dbeafe; }
.chunk-btn.disabled { background: #f1f5f9; color: #94a3b8; cursor: default; }
.badge { padding: 3px 10px; border-radius: 10px; font-size: 12px; }
.badge.pending { background: #fef9c3; color: #854d0e; }
.badge.done    { background: #dcfce7; color: #166534; }
.badge.error   { background: #fee2e2; color: #991b1b; }
.del-btn { background: none; border: none; cursor: pointer; font-size: 16px; }
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.popup { background: #fff; border-radius: 16px; width: 860px; max-width: 96vw; height: 85vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0,0,0,.2); overflow: hidden; }
.popup-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 24px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }
.popup-title { display: flex; align-items: center; gap: 12px; }
.popup-icon { font-size: 24px; }
.popup-filename { font-size: 15px; font-weight: 600; }
.popup-sub { font-size: 12px; color: #94a3b8; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.expand-all-btn { padding: 5px 14px; background: #f1f5f9; border: none; border-radius: 8px; font-size: 12px; cursor: pointer; }
.close-btn { background: #f1f5f9; border: none; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; font-size: 14px; }
.popup-search { display: flex; align-items: center; gap: 10px; padding: 12px 24px; border-bottom: 1px solid #f0f4f8; flex-shrink: 0; }
.search-input { flex: 1; padding: 8px 12px; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 13px; outline: none; }
.search-input:focus { border-color: #3b82f6; }
.search-count { font-size: 12px; color: #94a3b8; }
.popup-body { flex: 1; overflow-y: auto; padding: 16px 24px; display: flex; flex-direction: column; gap: 8px; scrollbar-width: thin; }
.popup-loading, .popup-empty { text-align: center; color: #94a3b8; padding: 40px 0; }
.chunk-item { border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; flex-shrink: 0; }
.chunk-item.open { border-color: #3b82f6; }
.chunk-header { display: flex; align-items: center; justify-content: space-between; padding: 11px 16px; background: #f8fafc; cursor: pointer; user-select: none; min-height: 44px; gap: 12px; }
.chunk-item.open .chunk-header { background: #eff6ff; }
.chunk-left { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.chunk-arrow { font-size: 11px; color: #94a3b8; width: 12px; flex-shrink: 0; }
.chunk-item.open .chunk-arrow { color: #3b82f6; }
.chunk-index { font-size: 13px; font-weight: 700; color: #3b82f6; min-width: 42px; background: #dbeafe; padding: 2px 8px; border-radius: 6px; text-align: center; flex-shrink: 0; }
.chunk-preview { font-size: 13px; color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.chunk-len { font-size: 12px; color: #94a3b8; flex-shrink: 0; }
.chunk-text { padding: 14px 16px; font-size: 13px; line-height: 1.75; color: #334155; white-space: pre-wrap; word-break: break-all; border-top: 1px solid #e2e8f0; max-height: 300px; overflow-y: auto; scrollbar-width: thin; }
.chunk-text :deep(mark) { background: #fef08a; color: #854d0e; border-radius: 3px; padding: 0 2px; }
.slide-enter-active, .slide-leave-active { transition: max-height .25s ease, opacity .2s ease; max-height: 300px; overflow: hidden; }
.slide-enter, .slide-leave-to { max-height: 0; opacity: 0; }
.knowledge-cell { text-align: center; }

/* 토글 스위치 */
.toggle { position: relative; display: inline-block; width: 36px; height: 20px; cursor: pointer; }
.toggle input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
  position: absolute; inset: 0;
  background: #cbd5e1; border-radius: 20px;
  transition: background .2s;
}
.toggle-slider:before {
  content: ""; position: absolute;
  width: 14px; height: 14px; left: 3px; bottom: 3px;
  background: #fff; border-radius: 50%;
  transition: transform .2s;
}
.toggle input:checked + .toggle-slider           { background: #3b82f6; }
.toggle input:checked + .toggle-slider:before    { transform: translateX(16px); }
.toggle input:disabled + .toggle-slider          { opacity: .4; cursor: not-allowed; }
</style>
