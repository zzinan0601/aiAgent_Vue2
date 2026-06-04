<template>
  <div class="msg-row" :class="msg.role">
    <div class="avatar" :class="msg.role">
      <template v-if="msg.role === 'assistant'">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2C12 2 13 8 16 11C19 14 22 12 22 12C22 12 16 13 13 16C10 19 12 22 12 22C12 22 11 16 8 13C5 10 2 12 2 12C2 12 8 11 11 8C14 5 12 2 12 2Z"/>
        </svg>
      </template>
      <template v-else>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="7" r="4"/>
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
      </template>
    </div>

    <div class="bubble">
      <button 
        v-if="msg.role === 'assistant'" 
        class="copy-msg-btn" 
        :title="copied ? '복사 완료!' : '서식 유지하여 복사'" 
        @click="copyRichText"
      >
        <template v-if="copied">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="copy-icon checked">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </template>
        <template v-else>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="copy-icon">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
        </template>
      </button>

      <div v-html="rendered" class="content" ref="msgBody" @click="onContentClick" />
      <div v-if="msg.sources && msg.sources.length" class="sources">
        <span class="src-label">출처:</span>
        <span v-for="(src, i) in msg.sources" :key="i" class="src-item">{{ src.filename }}</span>
      </div>
    </div>

    <div v-if="lightbox" class="lightbox" @click.self="lightbox = null">
      <div class="lightbox-inner" @click.stop>
        <img :src="lightbox" alt="차트" class="lightbox-img" />
        <div class="lightbox-actions">
          <a :href="lightbox" target="_blank" class="lb-btn">새 탭에서 열기</a>
          <a :href="lightbox" download class="lb-btn">다운로드</a>
          <button class="lb-btn lb-close" @click="lightbox = null">닫기</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from 'marked'

marked.use({
  renderer: {
    image(href, title, text) {
      return (
        '<img src="' + href + '"' +
        ' alt="' + (text || '차트') + '"' +
        ' class="chat-chart"' +
        ' data-src="' + href + '"' +
        ' title="클릭하여 크게 보기" />'
      )
    }
  }
})

export default {
  name: 'MessageItem',
  props: { msg: { type: Object, required: true } },
  data: () => ({ lightbox: null, copied: false }),
  computed: {
    rendered() { return marked.parse(this.msg.content || '') }
  },
  methods: {
    onContentClick(e) {
      if (e.target.tagName === 'IMG' && e.target.dataset.src) {
        this.lightbox = e.target.dataset.src
      }
    },
    async copyRichText() {
      if (this.copied) return
      
      const el = this.$refs.msgBody
      if (!el) return

      try {
        const styleText = `
          <style>
            .copied-content {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              font-size: 14.5px;
              line-height: 1.65;
              color: #334155;
            }
            .copied-content p {
              margin-top: 0;
              margin-bottom: 12px;
            }
            .copied-content ul, .copied-content ol {
              padding-left: 20px;
              margin: 8px 0;
            }
            .copied-content li {
              margin: 4px 0;
              line-height: 1.6;
            }
            .copied-content pre {
              background-color: #0f172a;
              color: #e2e8f0;
              padding: 14px;
              border-radius: 8px;
              overflow-x: auto;
              margin: 10px 0;
            }
            .copied-content code {
              font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace;
              font-size: 13px;
              background-color: #f1f5f9;
              color: #0f172a;
              padding: 2px 4px;
              border-radius: 4px;
            }
            .copied-content pre code {
              background-color: transparent;
              color: inherit;
              padding: 0;
              border-radius: 0;
            }
            .copied-content table {
              width: 100%;
              border-collapse: collapse;
              margin: 12px 0;
              font-size: 13px;
              border: 1px solid #e2e8f0;
            }
            .copied-content th {
              padding: 10px 14px;
              text-align: left;
              font-weight: 600;
              border-bottom: 2px solid #e2e8f0;
              border-right: 1px solid #e2e8f0;
              color: #475569;
              background-color: #f8fafc;
            }
            .copied-content td {
              padding: 9px 14px;
              border-bottom: 1px solid #e2e8f0;
              border-right: 1px solid #f1f5f9;
              color: #334155;
            }
            .copied-content tr:nth-child(even) td {
              background-color: #f8fafc;
            }
            .copied-content a {
              color: #2563eb;
              text-decoration: underline;
            }
          </style>
        `
        const htmlContent = `${styleText}<div class="copied-content">${el.innerHTML}</div>`
        const textContent = el.innerText || el.textContent

        const blobHtml = new Blob([htmlContent], { type: 'text/html' })
        const blobText = new Blob([textContent], { type: 'text/plain' })

        const data = [
          new window.ClipboardItem({
            'text/html': blobHtml,
            'text/plain': blobText
          })
        ]

        await navigator.clipboard.write(data)
        this.copied = true
        setTimeout(() => { this.copied = false }, 2000)
      } catch (err) {
        console.error('서식 복사 실패:', err)
        try {
          await navigator.clipboard.writeText(el.innerText || el.textContent)
          this.copied = true
          setTimeout(() => { this.copied = false }, 2000)
        } catch (e) {
          alert('복사 실패: ' + e.message)
        }
      }
    }
  }
}
</script>

<style scoped>
.msg-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 20px; }
.msg-row.user { flex-direction: row-reverse; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.avatar.assistant { background: rgba(37, 99, 235, 0.1); color: #2563eb; }
.avatar.user      { background: #e2e8f0; color: #475569; }
.avatar svg { width: 18px; height: 18px; }
.bubble {
  max-width: 75%; padding: 12px 18px; border-radius: 12px;
  font-size: 14px; line-height: 1.6; word-break: break-word;
  position: relative;
}
.user      .bubble { background: #2563eb; color: #ffffff; border-top-right-radius: 4px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15); }
.assistant .bubble { background: #ffffff; border: 1px solid #e2e8f0; border-top-left-radius: 4px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.015); color: #334155; padding-right: 42px; }
.copy-msg-btn {
  position: absolute; right: 10px; top: 10px;
  background: #ffffff; border: 1px solid #e2e8f0;
  border-radius: 6px; width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; opacity: 0.6;
  transition: all .2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.04);
  color: #64748b;
  z-index: 10;
}
.copy-msg-btn:hover {
  background: #f8fafc; border-color: rgba(37, 99, 235, 0.3);
  color: #2563eb;
  opacity: 1;
}
.copy-icon {
  width: 14px; height: 14px;
}
.copy-icon.checked {
  color: #10b981;
}
.content :deep(ul)  { padding-left: 18px; margin: 8px 0; }
.content :deep(ol)  { padding-left: 20px; margin: 8px 0; }
.content :deep(li)  { margin: 4px 0; line-height: 1.6; }
.content :deep(pre)  { background: #0f172a; color: #e2e8f0; padding: 14px; border-radius: 8px; overflow-x: auto; margin-top: 8px; }
.content :deep(code) { font-family: monospace; font-size: 13px; }
.content :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; }
.content :deep(thead) { background: #f8fafc; }
.content :deep(th) { padding: 10px 14px; text-align: left; font-weight: 600; border-bottom: 2px solid #e2e8f0; border-right: 1px solid #e2e8f0; color: #475569; }
.content :deep(th:last-child) { border-right: none; }
.content :deep(td) { padding: 9px 14px; border-bottom: 1px solid #e2e8f0; border-right: 1px solid #f1f5f9; color: #334155; }
.content :deep(td:last-child) { border-right: none; }
.content :deep(tbody tr:last-child td) { border-bottom: none; }
.content :deep(tbody tr:nth-child(even)) { background: #f8fafc; }
.content :deep(tbody tr:hover) { background: rgba(71, 85, 105, 0.02); }
.content :deep(.chat-chart) { max-width: 100%; border-radius: 10px; margin-top: 12px; cursor: zoom-in; border: 1px solid #e2e8f0; display: block; transition: opacity .15s; }
.content :deep(.chat-chart:hover) { opacity: .9; }
.sources { margin-top: 10px; padding-top: 10px; border-top: 1px solid #e2e8f0; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.src-label { font-size: 12px; color: #888; }
.src-item  { font-size: 12px; background: rgba(37, 99, 235, 0.05); color: #2563eb; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,.85); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.lightbox-inner { display: flex; flex-direction: column; align-items: center; gap: 14px; max-width: 90vw; }
.lightbox-img { max-width: 90vw; max-height: 80vh; border-radius: 12px; object-fit: contain; box-shadow: 0 8px 40px rgba(0,0,0,.5); }
.lightbox-actions { display: flex; gap: 10px; }
.lb-btn { padding: 8px 18px; background: rgba(255,255,255,.15); color: #fff; border: 1px solid rgba(255,255,255,.3); border-radius: 8px; text-decoration: none; font-size: 13px; cursor: pointer; }
.lb-btn:hover { background: rgba(255,255,255,.25); }
.lb-close { border-color: #ef4444; }
</style>
