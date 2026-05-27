import Vue       from 'vue'
import VueRouter from 'vue-router'
import ChatView  from '@/views/ChatView.vue'
import RagView   from '@/views/RagView.vue'

Vue.use(VueRouter)

const routes = [
  { path: '/',     redirect: '/chat' },
  { path: '/chat', component: ChatView, name: 'Chat' },
  { path: '/rag',  component: RagView,  name: 'RAG'  }
]

export default new VueRouter({ mode: 'history', routes })
