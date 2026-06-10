<template>
  <div class="rag-view">
    <div class="rag-inner">
      <h2 class="title">문서 관리</h2>

      <!-- RAG 설정 카드 -->
      <div class="settings-card">
        <h3 class="card-title">RAG 검색 및 임베딩 설정</h3>
        <div class="settings-grid">
          <div class="input-group">
            <label class="input-label">청크 크기 (Chunk Size)</label>
            <input v-model.number="settings.chunk_size" type="number" class="settings-input" min="100" max="2000" />
            <p class="input-desc">문서를 분할할 때의 최대 글자 수 단위입니다.</p>
          </div>
          <div class="input-group">
            <label class="input-label">오버랩 크기 (Overlap)</label>
            <input v-model.number="settings.chunk_overlap" type="number" class="settings-input" min="0" max="500" />
            <p class="input-desc">청크 간에 겹치는 중복 글자 수입니다.</p>
          </div>
          <div class="input-group">
            <label class="input-label">검색 후보 수 (Retrieve Top K)</label>
            <input v-model.number="settings.retrieve_top_k" type="number" class="settings-input" min="1" max="50" />
            <p class="input-desc">DB 벡터 검색 단계에서 조회할 청크 수입니다.</p>
          </div>
          <div class="input-group">
            <label class="input-label">최종 추천 수 (Rerank Top N)</label>
            <input v-model.number="settings.rerank_top_n" type="number" class="settings-input" min="1" max="10" />
            <p class="input-desc">리랭킹 알고리즘을 거쳐 LLM에 최종 전달될 개수입니다.</p>
          </div>
        </div>

        <!-- 하이브리드 검색 가중치 -->
        <h4 class="sub-title">하이브리드 검색 가중치</h4>
        <p class="sub-desc">Dense(의미 유사도)와 Sparse(키워드 매칭) 검색 비중을 조절합니다. 합계는 항상 1.0입니다.</p>
        <div class="weight-sliders">
          <div class="weight-group">
            <div class="weight-header">
              <label class="input-label">🧠 Dense (의미 유사도)</label>
              <span class="weight-value">{{ settings.dense_weight.toFixed(2) }}</span>
            </div>
            <input type="range" class="weight-slider dense-slider" min="0" max="1" step="0.05" :value="settings.dense_weight" @input="onDenseChange" />
          </div>
          <div class="weight-group">
            <div class="weight-header">
              <label class="input-label">🔑 Sparse (키워드 매칭)</label>
              <span class="weight-value">{{ settings.sparse_weight.toFixed(2) }}</span>
            </div>
            <input type="range" class="weight-slider sparse-slider" min="0" max="1" step="0.05" :value="settings.sparse_weight" @input="onSparseChange" />
          </div>
        </div>
        <div class="card-footer">
          <button class="save-settings-btn" :disabled="saving" @click="saveSettings">
            {{ saving ? '저장 중...' : '설정 저장' }}
          </button>
        </div>
      </div>

      <FileUpload @uploaded="onUploaded" />
      <div class="toolbar">
        <button class="refresh-btn" @click="loadDocuments">새로고침</button>
      </div>
      <DocList :documents="documents" @delete="onDelete" />
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import { fetchRagSettings, saveRagSettings } from '@/api/rag'
import FileUpload from '@/components/rag/FileUpload.vue'
import DocList    from '@/components/rag/DocList.vue'

export default {
  name: 'RagView',
  components: { FileUpload, DocList },
  data: () => ({
    settings: {
      chunk_size: 500,
      chunk_overlap: 50,
      retrieve_top_k: 10,
      rerank_top_n: 3,
      dense_weight: 0.7,
      sparse_weight: 0.3
    },
    saving: false
  }),
  computed: {
    ...mapState('rag', ['documents'])
  },
  async created() {
    this.loadDocuments()
    await this.loadSettings()
  },
  methods: {
    ...mapActions('rag', ['loadDocuments', 'removeDocument']),
    onUploaded() { this.loadDocuments(); this.startPolling() },
    onDelete(docId) { if (confirm('문서를 삭제할까요?')) this.removeDocument(docId) },
    startPolling() {
      const poll = setInterval(() => {
        const hasPending = this.documents.some(d => d.status === 'pending')
        if (!hasPending) { clearInterval(poll); return }
        this.loadDocuments()
      }, 3000)
    },
    async loadSettings() {
      try {
        const data = await fetchRagSettings()
        this.settings = {
          chunk_size: data.chunk_size,
          chunk_overlap: data.chunk_overlap,
          retrieve_top_k: data.retrieve_top_k,
          rerank_top_n: data.rerank_top_n,
          dense_weight: data.dense_weight ?? 0.7,
          sparse_weight: data.sparse_weight ?? 0.3
        }
      } catch (e) {
        console.error('RAG 설정 로드 실패:', e)
      }
    },
    async saveSettings() {
      if (this.settings.chunk_size < 100 || this.settings.chunk_size > 2000) {
        alert('청크 크기는 100 ~ 2000 사이로 설정해주세요.')
        return
      }
      if (this.settings.chunk_overlap < 0 || this.settings.chunk_overlap > 500) {
        alert('오버랩 크기는 0 ~ 500 사이로 설정해주세요.')
        return
      }
      if (this.settings.retrieve_top_k < 1 || this.settings.retrieve_top_k > 50) {
        alert('검색 후보 수는 1 ~ 50 사이로 설정해주세요.')
        return
      }
      if (this.settings.rerank_top_n < 1 || this.settings.rerank_top_n > 10) {
        alert('최종 추천 수는 1 ~ 10 사이로 설정해주세요.')
        return
      }
      if (this.settings.rerank_top_n > this.settings.retrieve_top_k) {
        alert('최종 추천 수는 검색 후보 수보다 작거나 같아야 합니다.')
        return
      }

      this.saving = true
      try {
        await saveRagSettings(this.settings)
        alert('RAG 설정이 저장되었습니다.')
      } catch (e) {
        alert('설정 저장 실패: ' + (e.response?.data?.detail || e.message))
      } finally {
        this.saving = false
      }
    },
    onDenseChange(e) {
      const v = parseFloat(e.target.value)
      this.settings.dense_weight  = Math.round(v * 100) / 100
      this.settings.sparse_weight = Math.round((1 - v) * 100) / 100
    },
    onSparseChange(e) {
      const v = parseFloat(e.target.value)
      this.settings.sparse_weight = Math.round(v * 100) / 100
      this.settings.dense_weight  = Math.round((1 - v) * 100) / 100
    }
  }
}
</script>

<style scoped>
.rag-view  { height: 100%; overflow-y: auto; padding: 40px 24px; background: #f8fafc; }
.rag-inner { max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
.title     { font-size: 22px; font-weight: 700; color: #0f172a; letter-spacing: -0.5px; margin: 0; }
.toolbar   { display: flex; justify-content: flex-end; }
.refresh-btn { padding: 8px 16px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; color: #475569; cursor: pointer; font-size: 13px; font-weight: 500; transition: all .15s ease; }
.refresh-btn:hover { background: #f1f5f9; color: #0f172a; border-color: #cbd5e1; }

/* RAG 설정 카드 */
.settings-card {
  background: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
}
.card-title {
  margin-top: 0; margin-bottom: 20px; color: #0f172a; font-weight: 600; font-size: 15px; border-left: 3.5px solid #2563eb; padding-left: 10px;
}
.settings-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;
}
@media (max-width: 640px) {
  .settings-grid { grid-template-columns: 1fr; }
}
.input-group {
  display: flex; flex-direction: column; gap: 6px;
}
.input-label {
  font-size: 13px; font-weight: 600; color: #334155;
}
.settings-input {
  padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13.5px; outline: none; background: #f8fafc; font-family: inherit; transition: border .15s, background .15s;
}
.settings-input:focus {
  border-color: #2563eb; background: #ffffff; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
.input-desc {
  font-size: 11.5px; color: #64748b; margin: 0;
}
.card-footer {
  display: flex; justify-content: flex-end; margin-top: 24px; border-top: 1px solid #f1f5f9; padding-top: 16px;
}
.save-settings-btn {
  padding: 9px 20px; background: #2563eb; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; color: #ffffff; cursor: pointer; transition: all .15s ease;
}
.save-settings-btn:hover:not(:disabled) {
  background: #1d4ed8;
}
.save-settings-btn:disabled {
  background: #cbd5e1; color: #94a3b8; cursor: not-allowed;
}

/* 하이브리드 검색 가중치 */
.sub-title {
  margin: 24px 0 4px 0; font-size: 14px; font-weight: 600; color: #334155;
}
.sub-desc {
  margin: 0 0 16px 0; font-size: 11.5px; color: #64748b;
}
.weight-sliders {
  display: flex; gap: 24px;
}
@media (max-width: 640px) {
  .weight-sliders { flex-direction: column; }
}
.weight-group {
  flex: 1; display: flex; flex-direction: column; gap: 8px;
}
.weight-header {
  display: flex; justify-content: space-between; align-items: center;
}
.weight-value {
  font-size: 14px; font-weight: 700; color: #0f172a; font-variant-numeric: tabular-nums;
}
.weight-slider {
  -webkit-appearance: none; appearance: none; width: 100%; height: 6px; border-radius: 3px; outline: none; cursor: pointer;
}
.weight-slider::-webkit-slider-thumb {
  -webkit-appearance: none; width: 18px; height: 18px; border-radius: 50%; cursor: pointer; border: 2px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.dense-slider  { background: linear-gradient(90deg, #e0e7ff, #2563eb); }
.dense-slider::-webkit-slider-thumb  { background: #2563eb; }
.sparse-slider { background: linear-gradient(90deg, #fce7f3, #db2777); }
.sparse-slider::-webkit-slider-thumb { background: #db2777; }
</style>
