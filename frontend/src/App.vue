<template>
  <div id="app">
    <nav class="navbar">
      <span class="logo">AI Agent</span>
      <div class="nav-links">
        <router-link to="/chat" class="nav-btn" active-class="active">💬 챗</router-link>
        <router-link to="/rag"  class="nav-btn" active-class="active">📂 RAG</router-link>
      </div>
    </nav>
    <router-view class="page" />
  </div>
</template>

<script>
export default { name: 'App' }
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Malgun Gothic', sans-serif; background: #f4f6fb; color: #222; }
#app { display: flex; flex-direction: column; height: 100vh; }
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; height: 52px; background: #1e2a3a; color: #fff; flex-shrink: 0;
}
.logo { font-size: 17px; font-weight: bold; }
.nav-links { display: flex; gap: 8px; }
.nav-btn {
  padding: 6px 18px; border-radius: 20px; color: #aac4e0;
  text-decoration: none; font-size: 14px; transition: background .2s;
}
.nav-btn:hover  { background: #2c3e55; }
.nav-btn.active { background: #3b82f6; color: #fff; }
.page { flex: 1; overflow: hidden; }
</style>
