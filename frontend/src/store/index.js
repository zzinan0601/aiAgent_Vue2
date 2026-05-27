import Vue  from 'vue'
import Vuex from 'vuex'
import chat from './chat'
import rag  from './rag'

Vue.use(Vuex)

export default new Vuex.Store({ modules: { chat, rag } })
