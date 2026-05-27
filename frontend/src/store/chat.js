import { fetchSessions, createSession, deleteSession, fetchMessages, fetchTools } from '@/api/chat'

export default {
  namespaced: true,
  state: () => ({
    sessions      : [],
    currentSession: null,
    messages      : [],
    loading       : false,
    tools         : [],
    useKnowledge  : false
  }),
  mutations: {
    SET_SESSIONS   (s, v) { s.sessions        = v },
    SET_CURRENT    (s, v) { s.currentSession  = v },
    SET_MESSAGES   (s, v) { s.messages        = v },
    SET_LOADING    (s, v) { s.loading         = v },
    SET_TOOLS      (s, v) { s.tools           = v },
    ADD_MESSAGE    (s, v) { s.messages.push(v)    },
    UPDATE_LAST_MSG(s, v) {
      const last = s.messages[s.messages.length - 1]
      if (last) last.content = v
    },
    // ← 추가: 마지막 메시지 내용 초기화
    CLEAR_LAST_MSG (s) {
        const last = s.messages[s.messages.length - 1]
        if (last) last.content = ''
    },
    SET_USE_KNOWLEDGE(s, v) { s.useKnowledge = v }
  },
  actions: {
    async loadSessions({ commit }) {
      const data = await fetchSessions()
      commit('SET_SESSIONS', data)
    },
    async newSession({ commit, dispatch, state }) {
    const session = await createSession('새 채팅', state.useKnowledge)  // ← useKnowledge 전달
    await dispatch('loadSessions')
    commit('SET_CURRENT', session)
    commit('SET_MESSAGES', [])
    },
    async selectSession({ commit }, session) {
      commit('SET_CURRENT', session)
      const messages = await fetchMessages(session.id)
      commit('SET_MESSAGES', messages)
    },
    async removeSession({ dispatch, commit, state }, sessionId) {
      await deleteSession(sessionId)
      if (state.currentSession && state.currentSession.id === sessionId) {
        commit('SET_CURRENT', null)
        commit('SET_MESSAGES', [])
      }
      await dispatch('loadSessions')
    },
    async loadTools({ commit }) {
      try {
        const tools = await fetchTools()
        commit('SET_TOOLS', tools)
      } catch (e) {
        console.error('툴 목록 로드 실패:', e)
        commit('SET_TOOLS', [])
      }
    }
  }
}
