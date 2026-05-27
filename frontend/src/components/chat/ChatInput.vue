<template>
  <div class="input-wrap">
    <!-- 모드 선택 -->
    <div class="mode-bar">
      <label v-for="opt in modeOptions" :key="opt.value" class="mode-opt" :class="{ active: mode === opt.value }">
        <input type="radio" v-model="mode" :value="opt.value" hidden />
        {{ opt.label }}
      </label>
    </div>

    <!-- @ 툴 자동완성 -->
    <div v-if="showToolMenu" class="tool-menu">
      <div class="tool-menu-title">🔧 툴 선택</div>
      <div
        v-for="t in filteredTools" :key="t.name"
        class="tool-menu-item"
        @mousedown.prevent="selectTool(t.name)"
      >
        <span class="tool-name">@{{ t.name }}</span>
        <span class="tool-desc">{{ t.description }}</span>
      </div>
      <div v-if="!filteredTools.length" class="tool-empty">일치하는 툴 없음</div>
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
        {{ disabled ? '⏳' : '전송 ▶' }}
      </button>
    </div>

    <div class="hint">💡 <code>@툴이름</code> 으로 특정 툴을 바로 호출할 수 있습니다</div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'ChatInput',
  props: { disabled: { type: Boolean, default: false } },
  data: () => ({
    text        : '',
    mode        : 'auto',
    showToolMenu: false,
    atQuery     : '',
    modeOptions : [
      { value: 'auto', label: '🤖 자동' },
      { value: 'chat', label: '💬 일반대화' },
      { value: 'tool', label: '🔧 툴 사용' }
    ]
  }),
  computed: {
    ...mapState('chat', ['tools']),
    placeholder() {
      return {
        auto: '메시지 입력... (@툴이름 으로 툴 직접 호출)',
        chat: '일반 대화 모드 — LLM 직접 응답',
        tool: '툴 사용 모드 — @툴이름 또는 자동 선택'
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
      this.$emit('send', { message: msg, mode: this.mode })
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
.input-wrap { background: #fff; border-top: 1px solid #e2e8f0; flex-shrink: 0; position: relative; }
.mode-bar { display: flex; gap: 6px; padding: 8px 20px 0; }
.mode-opt { padding: 4px 14px; border-radius: 14px; font-size: 12px; cursor: pointer; border: 1.5px solid #d1d9e6; color: #666; user-select: none; transition: all .15s; }
.mode-opt:hover  { border-color: #3b82f6; color: #3b82f6; }
.mode-opt.active { background: #3b82f6; border-color: #3b82f6; color: #fff; }
.tool-menu { position: absolute; bottom: 100%; left: 20px; right: 20px; background: #fff; border: 1.5px solid #e2e8f0; border-radius: 12px; box-shadow: 0 -8px 24px rgba(0,0,0,.1); overflow: hidden; z-index: 100; margin-bottom: 4px; }
.tool-menu-title { padding: 8px 14px; font-size: 11px; color: #94a3b8; background: #f8fafc; border-bottom: 1px solid #f0f4f8; font-weight: 600; }
.tool-menu-item { display: flex; align-items: center; gap: 10px; padding: 10px 14px; cursor: pointer; border-bottom: 1px solid #f8fafc; transition: background .12s; }
.tool-menu-item:last-child { border-bottom: none; }
.tool-menu-item:hover { background: #eff6ff; }
.tool-name { font-size: 13px; font-weight: 600; color: #2563eb; min-width: 160px; flex-shrink: 0; }
.tool-desc { font-size: 12px; color: #64748b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tool-empty { padding: 12px 14px; font-size: 13px; color: #94a3b8; }
.input-area { display: flex; align-items: flex-end; gap: 10px; padding: 10px 20px 8px; }
.input-box { flex: 1; padding: 10px 14px; border: 1.5px solid #d1d9e6; border-radius: 12px; font-size: 14px; resize: none; outline: none; font-family: inherit; line-height: 1.5; transition: border .2s; }
.input-box:focus    { border-color: #3b82f6; }
.input-box:disabled { background: #f8fafc; }
.send-btn { padding: 10px 20px; background: #3b82f6; color: #fff; border: none; border-radius: 12px; font-size: 14px; cursor: pointer; white-space: nowrap; flex-shrink: 0; transition: background .2s; }
.send-btn:hover:not(:disabled) { background: #2563eb; }
.send-btn:disabled { background: #9bb8d8; cursor: not-allowed; }
.hint { padding: 4px 20px 10px; font-size: 11px; color: #94a3b8; }
.hint code { background: #f1f5f9; padding: 1px 5px; border-radius: 4px; font-size: 11px; color: #3b82f6; }
</style>
