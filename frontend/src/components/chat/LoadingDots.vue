<template>
  <div class="loading-wrap">
    <span class="dot" v-for="i in 3" :key="i" :style="{ animationDelay: (i-1)*0.2 + 's' }" />
    <span v-if="status" class="status-text">{{ status }}</span>
  </div>
</template>

<script>
export default {
  name: 'LoadingDots',
  props: { status: { type: String, default: '' } }
}
</script>

<style scoped>
.loading-wrap { display: flex; align-items: center; gap: 5px; padding: 12px 16px; }
.dot {
  width: 8px; height: 8px; border-radius: 50%; background: #3b82f6;
  animation: bounce .9s infinite ease-in-out;
}
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: .4; }
  40%           { transform: translateY(-8px); opacity: 1; }
}
.status-text { font-size: 12px; color: #888; margin-left: 6px; }
</style>
