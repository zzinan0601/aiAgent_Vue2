<template>
  <div class="upload-box">
    <h3>📁 파일 업로드</h3>
    <p class="hint">PDF, DOCX, TXT 파일을 지원합니다</p>
    <div class="drop-zone" :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
      @click="$refs.fileInput.click()"
    >
      <span v-if="!uploading">📂 클릭하거나 파일을 드래그하세요</span>
      <span v-else>⏳ 업로드 중... {{ progress }}%</span>
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
  data: () => ({ dragging: false, uploading: false, progress: 0, resultMsg: '', resultType: 'success' }),
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
        await uploadFile(file, p => { this.progress = p })
        this.resultMsg  = '✅ ' + file.name + ' 업로드 완료! 임베딩이 백그라운드에서 진행됩니다.'
        this.resultType = 'success'
        this.$emit('uploaded')
      } catch {
        this.resultMsg  = '❌ 업로드 실패. 파일 형식을 확인하세요.'
        this.resultType = 'error'
      } finally {
        this.uploading = false
      }
    }
  }
}
</script>

<style scoped>
.upload-box { background: #fff; border-radius: 12px; padding: 24px; }
h3 { margin-bottom: 6px; }
.hint { color: #888; font-size: 13px; margin-bottom: 16px; }
.drop-zone { border: 2px dashed #c0ccda; border-radius: 10px; padding: 36px; text-align: center; color: #666; cursor: pointer; transition: all .2s; font-size: 14px; }
.drop-zone:hover, .drop-zone.dragging { border-color: #3b82f6; background: #eff6ff; color: #3b82f6; }
.progress-bar  { height: 6px; background: #e2e8f0; border-radius: 4px; margin-top: 12px; overflow: hidden; }
.progress-fill { height: 100%; background: #3b82f6; transition: width .3s; }
.result { margin-top: 12px; padding: 10px 14px; border-radius: 8px; font-size: 13px; }
.result.success { background: #f0fdf4; color: #16a34a; }
.result.error   { background: #fef2f2; color: #dc2626; }
</style>
