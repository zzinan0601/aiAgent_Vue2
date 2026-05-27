import { fetchDocuments, deleteDocument } from '@/api/rag'

export default {
  namespaced: true,
  state: () => ({
    documents: [],
    uploading: false
  }),
  mutations: {
    SET_DOCUMENTS(s, v) { s.documents = v },
    SET_UPLOADING(s, v) { s.uploading = v }
  },
  actions: {
    async loadDocuments({ commit }) {
      const data = await fetchDocuments()
      commit('SET_DOCUMENTS', data)
    },
    async removeDocument({ dispatch }, docId) {
      await deleteDocument(docId)
      await dispatch('loadDocuments')
    }
  }
}
