<template>
  <div id="app">
    <nav class="navbar">
      <span class="logo">AI Agent</span>
      <div class="nav-links">
        <router-link to="/chat" class="nav-btn" active-class="active">채팅</router-link>
        <router-link to="/rag"  class="nav-btn" active-class="active">문서 관리</router-link>
      </div>
    </nav>
    <router-view class="page" />
  </div>
</template>

<script>
export default { name: 'App' }
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Outfit:wght@300;400;500;600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Outfit', 'Noto Sans KR', sans-serif; background: #f8fafc; color: #1e293b; -webkit-font-smoothing: antialiased; }
#app { display: flex; flex-direction: column; height: 100vh; }
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 28px; height: 56px; background: #ffffff; color: #0f172a; flex-shrink: 0;
  border-bottom: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.01);
}
.logo { font-size: 18px; font-weight: 700; color: #334155; letter-spacing: -0.5px; }
.nav-links { display: flex; gap: 8px; }
.nav-btn {
  padding: 6px 16px; border-radius: 8px; color: #475569;
  text-decoration: none; font-size: 14px; font-weight: 500; transition: all .2s ease;
}
.nav-btn:hover  { background: #f1f5f9; color: #0f172a; }
.nav-btn.active { background: rgba(37, 99, 235, 0.08); color: #2563eb; }
.page { flex: 1; overflow: hidden; }
</style>
