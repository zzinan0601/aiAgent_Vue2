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
      <div v-html="rendered" class="content" @click="onContentClick" />
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
  data: () => ({ lightbox: null }),
  computed: {
    rendered() { return marked.parse(this.msg.content || '') }
  },
  methods: {
    onContentClick(e) {
      if (e.target.tagName === 'IMG' && e.target.dataset.src) {
        this.lightbox = e.target.dataset.src
      }
    }
  }
}
</script>

<style scoped>
.msg-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 16px; }
.msg-row.user { flex-direction: row-reverse; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.avatar.assistant { background: #dbeafe; color: #2563eb; }
.avatar.user      { background: #e2e8f0; color: #475569; }
.avatar svg { width: 20px; height: 20px; }
.bubble {
  max-width: 72%; padding: 12px 16px; border-radius: 14px;
  font-size: 14px; line-height: 1.6; word-break: break-word;
}
.user      .bubble { background: #3b82f6; color: #fff; border-bottom-right-radius: 4px; }
.assistant .bubble { background: #fff; border: 1px solid #e2e8f0; border-bottom-left-radius: 4px; }
.content :deep(ul)  { padding-left: 18px; margin: 8px 0; }
.content :deep(ol)  { padding-left: 20px; margin: 8px 0; }
.content :deep(li)  { margin: 4px 0; line-height: 1.6; }
.content :deep(pre)  { background: #1e2a3a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow-x: auto; margin-top: 8px; }
.content :deep(code) { font-family: monospace; font-size: 13px; }
.content :deep(table) { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; }
.content :deep(thead) { background: #f1f5f9; }
.content :deep(th) { padding: 10px 14px; text-align: left; font-weight: 600; border-bottom: 2px solid #cbd5e1; border-right: 1px solid #e2e8f0; }
.content :deep(th:last-child) { border-right: none; }
.content :deep(td) { padding: 9px 14px; border-bottom: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; }
.content :deep(td:last-child) { border-right: none; }
.content :deep(tbody tr:last-child td) { border-bottom: none; }
.content :deep(tbody tr:nth-child(even)) { background: #f8fafc; }
.content :deep(tbody tr:hover) { background: #eff6ff; }
.content :deep(.chat-chart) { max-width: 100%; border-radius: 10px; margin-top: 12px; cursor: zoom-in; border: 1px solid #e2e8f0; display: block; transition: opacity .15s; }
.content :deep(.chat-chart:hover) { opacity: .9; }
.sources { margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.src-label { font-size: 12px; color: #888; }
.src-item  { font-size: 12px; background: #eef2ff; color: #3b82f6; padding: 2px 8px; border-radius: 10px; }
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,.85); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.lightbox-inner { display: flex; flex-direction: column; align-items: center; gap: 14px; max-width: 90vw; }
.lightbox-img { max-width: 90vw; max-height: 80vh; border-radius: 12px; object-fit: contain; box-shadow: 0 8px 40px rgba(0,0,0,.5); }
.lightbox-actions { display: flex; gap: 10px; }
.lb-btn { padding: 8px 18px; background: rgba(255,255,255,.15); color: #fff; border: 1px solid rgba(255,255,255,.3); border-radius: 8px; text-decoration: none; font-size: 13px; cursor: pointer; }
.lb-btn:hover { background: rgba(255,255,255,.25); }
.lb-close { border-color: #f87171; }
</style>
