<template>
  <div class="input-wrap">
    <!-- 모드 선택 -->
    <div class="mode-bar">
      <div class="mode-options">
        <label v-for="opt in modeOptions" :key="opt.value" class="mode-opt" :class="{ active: mode === opt.value }">
          <input type="radio" v-model="mode" :value="opt.value" hidden />
          {{ opt.label }}
        </label>
      </div>
      <div class="model-selector">
        <select v-model="selectedModel" class="model-select" :disabled="disabled">
          <option v-for="m in modelList" :key="m" :value="m">{{ m }}</option>
        </select>
      </div>
    </div>

    <!-- @ 툴 자동완성 -->
    <div v-if="showToolMenu" class="tool-menu">
      <div class="tool-menu-title">도구 선택</div>
      <div
        v-for="t in filteredTools" :key="t.name"
        class="tool-menu-item"
        @mousedown.prevent="selectTool(t.name)"
      >
        <span class="tool-name">@{{ t.name }}</span>
        <span class="tool-desc">{{ t.description }}</span>
      </div>
      <div v-if="!filteredTools.length" class="tool-empty">일치하는 도구 없음</div>
    </div>

    <!-- 입력창 -->
    <div class="input-area">
      <textarea
        v-model="text"
        class="input-box"
        :placeholder="placeholder"
        rows="1"
        :disabled="disabled"
        @keydown.enter.exact.prevent="send"
        @keydown.esc="showToolMenu = false"
        @input="onInput"
        ref="textarea"
      />
      <button class="send-btn" @click="send" :disabled="disabled || !text.trim()">
        {{ disabled ? '대기' : '전송' }}
      </button>
    </div>

    <div class="hint"><code>@도구이름</code> 형식을 입력하면 특정 도구를 지정하여 실행할 수 있습니다.</div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { fetchOllamaModels } from '@/api/chat'

export default {
  name: 'ChatInput',
  props: { disabled: { type: Boolean, default: false } },
  data: () => ({
    text         : '',
    mode         : 'auto',
    showToolMenu : false,
    atQuery      : '',
    selectedModel: '',
    modelList    : [],
    modeOptions  : [
      { value: 'auto', label: '자동' },
      { value: 'chat', label: '대화' },
      { value: 'tool', label: '도구 실행' }
    ]
  }),
  async created() {
    try {
      const data = await fetchOllamaModels()
      this.modelList = (data.models || []).map(m => m.name)
      if (this.modelList.length > 0) {
        this.selectedModel = this.modelList[0]
      }
    } catch (e) {
      console.error('모델 목록 로드 실패:', e)
    }
  },
  computed: {
    ...mapState('chat', ['tools']),
    placeholder() {
      return {
        auto: '메시지를 입력하세요... (@도구이름 형식으로 직접 호출 가능)',
        chat: '대화 모드 — 인공지능이 직접 답변합니다.',
        tool: '도구 실행 모드 — 도구 명칭을 자동 혹은 수동으로 지정합니다.'
      }[this.mode]
    },
    filteredTools() {
      const q = this.atQuery.toLowerCase()
      if (!q) return this.tools
      return this.tools.filter(t => t.name.includes(q))
    }
  },
  methods: {
    onInput() {
      this.autoResize()
      const val    = this.text
      const cursor = this.$refs.textarea.selectionStart
      const before = val.slice(0, cursor)
      const match  = before.match(/@(\w*)$/)
      if (match) {
        this.atQuery      = match[1]
        this.showToolMenu = true
        this.mode         = 'tool'
      } else {
        this.showToolMenu = false
        this.atQuery      = ''
      }
    },
    selectTool(toolName) {
      const val      = this.text
      const cursor   = this.$refs.textarea.selectionStart
      const before   = val.slice(0, cursor)
      const after    = val.slice(cursor)
      const replaced = before.replace(/@\w*$/, '@' + toolName + ' ')
      this.text         = replaced + after
      this.showToolMenu = false
      this.mode         = 'tool'
      this.$nextTick(() => {
        this.$refs.textarea.focus()
        this.$refs.textarea.setSelectionRange(replaced.length, replaced.length)
      })
    },
    send() {
      const msg = this.text.trim()
      if (!msg || this.disabled) return
      this.$emit('send', { message: msg, mode: this.mode, model: this.selectedModel })
      this.text         = ''
      this.showToolMenu = false
      this.$nextTick(() => { this.$refs.textarea.style.height = 'auto' })
    },
    autoResize() {
      const el = this.$refs.textarea
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 120) + 'px'
    }
  }
}
</script>

<style scoped>
.input-wrap { background: #ffffff; border-top: 1px solid #e2e8f0; flex-shrink: 0; position: relative; box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.015); }
.mode-bar { display: flex; justify-content: space-between; align-items: center; gap: 6px; padding: 10px 24px 0; }
.mode-options { display: flex; gap: 6px; }
.model-selector { display: flex; align-items: center; }
.model-select { padding: 5px 10px; border-radius: 8px; font-size: 12px; border: 1px solid #e2e8f0; color: #475569; background: #ffffff; cursor: pointer; outline: none; font-weight: 500; transition: all .15s ease; max-width: 200px; }
.model-select:hover { border-color: #cbd5e1; }
.model-select:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.08); }
.model-select:disabled { background: #f1f5f9; color: #94a3b8; cursor: not-allowed; }
.mode-opt { padding: 5px 15px; border-radius: 20px; font-size: 12px; cursor: pointer; border: 1px solid #e2e8f0; color: #64748b; background: #ffffff; user-select: none; transition: all .15s ease; font-weight: 500; }
.mode-opt:hover  { border-color: #cbd5e1; color: #334155; }
.mode-opt.active { background: rgba(37, 99, 235, 0.08); border-color: rgba(37, 99, 235, 0.2); color: #2563eb; }
.tool-menu { position: absolute; bottom: 100%; left: 24px; right: 24px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; box-shadow: 0 -10px 30px rgba(0,0,0,.08); overflow: hidden; z-index: 100; margin-bottom: 6px; }
.tool-menu-title { padding: 8px 14px; font-size: 11px; color: #94a3b8; background: #f8fafc; border-bottom: 1px solid #f1f5f9; font-weight: 600; }
.tool-menu-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #f8fafc; transition: background .12s; }
.tool-menu-item:last-child { border-bottom: none; }
.tool-menu-item:hover { background: rgba(37, 99, 235, 0.04); }
.tool-name { font-size: 13px; font-weight: 600; color: #2563eb; min-width: 160px; flex-shrink: 0; }
.tool-desc { font-size: 12px; color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tool-empty { padding: 12px 14px; font-size: 13px; color: #94a3b8; }
.input-area { display: flex; align-items: flex-end; gap: 10px; padding: 10px 24px 8px; }
.input-box { flex: 1; padding: 11px 16px; border: 1px solid #e2e8f0; border-radius: 12px; font-size: 14px; resize: none; outline: none; font-family: inherit; line-height: 1.5; transition: all .2s ease; background: #f8fafc; }
.input-box:focus    { border-color: #2563eb; background: #ffffff; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12); }
.input-box:disabled { background: #f1f5f9; color: #94a3b8; }
.send-btn { padding: 10px 22px; background: #2563eb; color: #ffffff; border: none; border-radius: 12px; font-size: 14px; font-weight: 500; cursor: pointer; white-space: nowrap; flex-shrink: 0; transition: all .15s ease; }
.send-btn:hover:not(:disabled) { background: #1d4ed8; }
.send-btn:disabled { background: #e2e8f0; color: #94a3b8; cursor: not-allowed; }
.hint { padding: 4px 24px 12px; font-size: 11px; color: #94a3b8; }
.hint code { background: rgba(37, 99, 235, 0.05); padding: 1px 5px; border-radius: 4px; font-size: 11px; color: #2563eb; }
</style>
