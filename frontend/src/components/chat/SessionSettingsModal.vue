<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-popup">
      <!-- 헤더 -->
      <div class="modal-header">
        <div class="modal-title">
          <div>
            <h3>세션 설정</h3>
            <p class="modal-subtitle">이 채팅방의 전용 역할과 예시를 지정합니다.</p>
          </div>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <!-- 1. 채팅방 제목 수정 추가 -->
        <div class="section">
          <label class="section-label">채팅방 제목</label>
          <input
            v-model="localTitle"
            type="text"
            class="input-field-title"
            placeholder="채팅방 제목을 입력하세요..."
          />
        </div>

        <!-- 2. 시스템 프롬프트 -->
        <div class="section">
          <label class="section-label">시스템 프롬프트 (System Prompt)</label>
          <textarea
            v-model="localSystemPrompt"
            class="textarea-box"
            placeholder="예: 당신은 사내 지식 Q&A 비서입니다. 제공된 문서 내용만 근거하여 답하세요."
            rows="5"
          />
        </div>

        <!-- 3. 답변 다양성 (Temperature) -->
        <div class="section">
          <div class="slider-header">
            <label class="section-label">답변 온감 (Temperature)</label>
            <span class="slider-value">{{ localTemperature.toFixed(1) }}</span>
          </div>
          <input
            v-model.number="localTemperature"
            type="range"
            min="0.0"
            max="1.0"
            step="0.1"
            class="slider-input"
          />
          <p class="slider-desc">
            낮은 값(예: 0.2)은 사실에 기반한 정밀한 답변에, 높은 값(예: 0.8)은 다양하고 유연한 답변에 적합합니다.
          </p>
        </div>

        <!-- 3. Few-shot 예시 -->
        <div class="section">
          <div class="section-header">
            <label class="section-label">대화 예시 (Few-shot Examples)</label>
            <button class="add-example-btn" @click="addFewShot">예시 추가</button>
          </div>

          <div class="few-shot-list">
            <div v-for="(fs, idx) in localFewShots" :key="idx" class="few-shot-card">
              <div class="few-shot-card-header">
                <span class="few-shot-index">예시 {{ idx + 1 }}</span>
                <button class="del-example-btn" @click="removeFewShot(idx)">삭제</button>
              </div>
              <div class="few-shot-inputs">
                <div class="input-group">
                  <span class="input-prefix user">질문</span>
                  <input
                    v-model="fs.user"
                    type="text"
                    class="input-field"
                    placeholder="예시 질문을 입력하세요..."
                  />
                </div>
                <div class="input-group">
                  <span class="input-prefix assistant">답변</span>
                  <textarea
                    v-model="fs.assistant"
                    class="input-field textarea-field"
                    rows="2"
                    placeholder="원하는 형태의 모범 답변을 입력하세요..."
                  />
                </div>
              </div>
            </div>
            <div v-if="!localFewShots.length" class="few-shot-empty">
              등록된 대화 예시가 없습니다.
            </div>
          </div>
        </div>
      </div>

      <!-- 푸터 -->
      <div class="modal-footer">
        <button class="cancel-btn" @click="$emit('close')">취소</button>
        <button class="save-btn" :disabled="saving" @click="saveSettings">
          {{ saving ? '저장 중...' : '설정 저장하기' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SessionSettingsModal',
  props: {
    session: { type: Object, required: true }
  },
  data() {
    return {
      localTitle: '',
      localSystemPrompt: '',
      localFewShots: [],
      localTemperature: 0.7,
      saving: false
    }
  },
  created() {
    this.localTitle = this.session.title || ''
    this.localSystemPrompt = this.session.system_prompt || ''
    this.localTemperature = this.session.temperature !== undefined ? this.session.temperature : 0.7
    try {
      this.localFewShots = this.session.few_shots
        ? JSON.parse(this.session.few_shots)
        : []
    } catch {
      this.localFewShots = []
    }
  },
  methods: {
    addFewShot() {
      this.localFewShots.push({ user: '', assistant: '' })
    },
    removeFewShot(idx) {
      this.localFewShots.splice(idx, 1)
    },
    async saveSettings() {
      // 빈 입력 필터링
      const filteredFewShots = this.localFewShots.filter(
        fs => fs.user.trim() || fs.assistant.trim()
      )

      this.saving = true
      try {
        await this.$store.dispatch('chat/saveSessionSettings', {
          sessionId: this.session.id,
          title: this.localTitle,
          systemPrompt: this.localSystemPrompt,
          fewShots: JSON.stringify(filteredFewShots),
          temperature: this.localTemperature
        })
        this.$emit('saved')
        this.$emit('close')
      } catch (e) {
        alert('설정 저장 실패: ' + (e.response?.data?.detail || e.message))
      } finally {
        this.saving = false
      }
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
  width: 600px; max-width: 94vw;
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
.modal-title h3 {
  font-size: 16px; font-weight: 600; color: #0f172a;
}
.modal-subtitle {
  font-size: 12px; color: #64748b; margin-top: 2px;
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
  display: flex; flex-direction: column; gap: 20px;
}

.section {
  display: flex; flex-direction: column; gap: 8px;
}
.section-header {
  display: flex; align-items: center; justify-content: space-between;
}
.section-label {
  font-size: 13.5px; font-weight: 600; color: #334155;
}

.textarea-box {
  width: 100%; padding: 12px;
  border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 13.5px; line-height: 1.5; outline: none;
  resize: vertical; font-family: inherit;
  transition: border .15s; background: #f8fafc;
}
.textarea-box:focus {
  border-color: #475569; background: #ffffff;
  box-shadow: 0 0 0 3px rgba(71, 85, 105, 0.12);
}

.input-field-title {
  width: 100%; padding: 10px 14px;
  border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 13.5px; outline: none; background: #f8fafc;
  font-family: inherit; transition: border .15s;
}
.input-field-title:focus {
  border-color: #475569; background: #ffffff;
  box-shadow: 0 0 0 3px rgba(71, 85, 105, 0.12);
}

.add-example-btn {
  padding: 5px 12px;
  background: rgba(71, 85, 105, 0.08);
  border: none; border-radius: 6px;
  font-size: 12px; font-weight: 600; color: #475569;
  cursor: pointer; transition: background .15s;
}
.add-example-btn:hover {
  background: rgba(71, 85, 105, 0.15);
}

.few-shot-list {
  display: flex; flex-direction: column; gap: 10px; margin-top: 6px;
}
.few-shot-card {
  border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 12px; background: #f8fafc;
}
.few-shot-card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.few-shot-index {
  font-size: 12px; font-weight: 700; color: #475569;
}
.del-example-btn {
  background: none; border: none;
  color: #94a3b8; font-size: 11.5px;
  cursor: pointer; font-weight: 500;
  transition: color .15s;
}
.del-example-btn:hover {
  color: #ef4444;
}

.few-shot-inputs {
  display: flex; flex-direction: column; gap: 8px;
}
.input-group {
  display: flex; align-items: flex-start; gap: 8px;
}
.input-prefix {
  font-size: 11px; font-weight: 700;
  padding: 3px 8px; border-radius: 4px;
  width: 44px; text-align: center; margin-top: 4px; flex-shrink: 0;
}
.input-prefix.user {
  background: rgba(71, 85, 105, 0.08); color: #475569;
}
.input-prefix.assistant {
  background: #f1f5f9; color: #475569;
}
.input-field {
  flex: 1; padding: 8px 12px;
  border: 1px solid #e2e8f0; border-radius: 6px;
  font-size: 13px; outline: none; background: #ffffff;
  font-family: inherit; transition: border .15s;
}
.input-field:focus {
  border-color: #475569;
}
.textarea-field {
  resize: vertical;
}

.few-shot-empty {
  text-align: center; font-size: 12px;
  color: #94a3b8; padding: 20px;
  border: 1px dashed #cbd5e1; border-radius: 10px;
}

.modal-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 16px 24px; border-top: 1px solid #e2e8f0;
  flex-shrink: 0; background: #f8fafc;
}
.cancel-btn {
  padding: 8px 16px; background: #ffffff;
  border: 1px solid #e2e8f0; border-radius: 8px;
  font-size: 13.5px; font-weight: 500; color: #475569;
  cursor: pointer; transition: all .15s;
}
.cancel-btn:hover {
  background: #f1f5f9; color: #0f172a;
}
.save-btn {
  padding: 8px 18px; background: #475569;
  border: none; border-radius: 8px;
  font-size: 13.5px; font-weight: 500; color: #ffffff;
  cursor: pointer; transition: all .15s;
}
.save-btn:hover:not(:disabled) {
  background: #334155;
}
.save-btn:disabled {
  background: #e2e8f0; color: #94a3b8; cursor: not-allowed;
}

/* 템퍼레이처 슬라이더 */
.slider-header {
  display: flex; justify-content: space-between; align-items: center;
}
.slider-value {
  font-size: 13px; font-weight: 700; color: #2563eb;
  background: rgba(37, 99, 235, 0.08); padding: 2px 8px; border-radius: 6px;
}
.slider-input {
  -webkit-appearance: none; width: 100%; height: 6px; background: #e2e8f0; border-radius: 3px; outline: none; margin: 8px 0;
}
.slider-input::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none; width: 16px; height: 16px; border-radius: 50%; background: #2563eb; cursor: pointer; transition: transform .1s;
}
.slider-input::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}
.slider-desc {
  font-size: 12px; color: #64748b; margin-top: 2px;
}
</style>
