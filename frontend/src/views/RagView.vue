<template>
  <div class="rag-view">
    <div class="rag-inner">
      <h2 class="title">📂 RAG 문서 관리</h2>
      <FileUpload @uploaded="onUploaded" />
      <div class="toolbar">
        <button class="refresh-btn" @click="loadDocuments">🔄 목록 새로고침</button>
      </div>
      <DocList :documents="documents" @delete="onDelete" />
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import FileUpload from '@/components/rag/FileUpload.vue'
import DocList    from '@/components/rag/DocList.vue'

export default {
  name: 'RagView',
  components: { FileUpload, DocList },
  computed: {
    ...mapState('rag', ['documents'])
  },
  created() { this.loadDocuments() },
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
    }
  }
}
</script>

<style scoped>
.rag-view  { height: 100%; overflow-y: auto; padding: 32px; background: #f4f6fb; }
.rag-inner { max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
.title     { font-size: 20px; font-weight: bold; }
.toolbar   { display: flex; justify-content: flex-end; }
.refresh-btn { padding: 8px 16px; background: #fff; border: 1px solid #d1d9e6; border-radius: 8px; cursor: pointer; font-size: 13px; }
.refresh-btn:hover { background: #eff6ff; }
</style>
