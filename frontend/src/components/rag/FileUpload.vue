<template>
  <div class="upload-box">
    <h3>파일 업로드</h3>
    <p class="hint">PDF, DOCX, TXT 파일을 지원합니다.</p>
    <div class="metadata-form" v-if="!uploading">
      <div class="input-row">
        <input v-model="metadata.category" type="text" placeholder="카테고리 (옵션. 예: 규정, 매뉴얼)" class="meta-input" />
      </div>
    </div>
    <div class="drop-zone" :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
      @click="$refs.fileInput.click()"
    >
      <span v-if="!uploading">클릭하거나 파일을 여기로 드래그하세요.</span>
      <span v-else>업로드 중... {{ progress }}%</span>
    </div>
    <input ref="fileInput" type="file" accept=".pdf,.docx,.txt" style="display:none" @change="onFileChange" />
    <div v-if="uploading" class="progress-bar">
      <div class="progress-fill" :style="{ width: progress + '%' }" />
    </div>
    <div v-if="resultMsg" class="result" :class="resultType">{{ resultMsg }}</div>
  </div>
</template>

<script>
import { uploadFile } from '@/api/rag'

export default {
  name: 'FileUpload',
  data: () => ({ dragging: false, uploading: false, progress: 0, resultMsg: '', resultType: 'success', metadata: { category: '' } }),
  methods: {
    onDrop(e) {
      this.dragging = false
      const file = e.dataTransfer.files[0]
      if (file) this.upload(file)
    },
    onFileChange(e) {
      const file = e.target.files[0]
      if (file) this.upload(file)
      e.target.value = ''
    },
    async upload(file) {
      this.uploading = true
      this.progress  = 0
      this.resultMsg = ''
      try {
        const metaPayload = {
          last_modified_date: new Date(file.lastModified).toISOString()
        }
        if (this.metadata.category) metaPayload.category = this.metadata.category

        await uploadFile(file, metaPayload, p => { this.progress = p })
        this.resultMsg  = file.name + ' 업로드 완료. 문서 처리가 백그라운드에서 진행됩니다.'
        this.resultType = 'success'
        this.metadata = { category: '' }
        this.$emit('uploaded')
      } catch {
        this.resultMsg  = '업로드 실패. 파일 형식을 확인하세요.'
        this.resultType = 'error'
      } finally {
        this.uploading = false
      }
    }
  }
}
</script>

<style scoped>
.upload-box { background: #ffffff; border-radius: 12px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02); }
h3 { margin-bottom: 6px; color: #0f172a; font-weight: 600; font-size: 16px; }
.hint { color: #64748b; font-size: 13px; margin-bottom: 16px; }
.drop-zone { border: 1px dashed #cbd5e1; border-radius: 10px; padding: 36px; text-align: center; color: #475569; cursor: pointer; transition: all .2s ease; font-size: 14px; background: #f8fafc; }
.drop-zone:hover, .drop-zone.dragging { border-color: #475569; background: rgba(71, 85, 105, 0.03); color: #334155; }
.progress-bar  { height: 6px; background: #e2e8f0; border-radius: 4px; margin-top: 12px; overflow: hidden; }
.progress-fill { height: 100%; background: #475569; transition: width .3s; }
.result { margin-top: 12px; padding: 10px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; }
.result.success { background: #f0fdf4; color: #15803d; border: 1px solid #dcfce7; }
.result.error   { background: #fef2f2; color: #b91c1c; border: 1px solid #fee2e2; }
.metadata-form { margin-bottom: 16px; }
.input-row { display: flex; gap: 12px; }
.meta-input { flex: 1; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 13px; outline: none; background: #f8fafc; transition: border .15s, background .15s; }
.meta-input:focus { border-color: #475569; background: #ffffff; }
</style>
