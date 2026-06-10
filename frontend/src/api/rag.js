import api from './index'

export const fetchDocuments = async () => {
  const res = await api.get('/rag/list')
  return res.data
}

export const uploadFile = async (file, metadata, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  if (metadata && Object.keys(metadata).length > 0) {
    form.append('metadata', JSON.stringify(metadata))
  }
  const res = await api.post('/rag/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => { if (onProgress) onProgress(Math.round(e.loaded / e.total * 100)) }
  })
  return res.data
}

export const fetchEmbedStatus = async (docId) => {
  const res = await api.get('/rag/status/' + docId)
  return res.data
}

export const fetchChunks = async (docId) => {
  const res = await api.get('/rag/' + docId + '/chunks')
  return res.data
}

export const deleteDocument = async (docId) => {
  await api.delete('/rag/' + docId)
}

// 기존 코드 하단에 추가
export const toggleKnowledge = async (docId, isKnowledge) => {
  const res = await api.patch(
    '/rag/' + docId + '/knowledge?is_knowledge=' + isKnowledge
  )
  return res.data
}

export const fetchKnowledgeDocs = async () => {
  const res = await api.get('/rag/knowledge/list')
  return res.data
}

export const fetchRagSettings = async () => {
  const res = await api.get('/rag/settings')
  return res.data
}

export const saveRagSettings = async (settings) => {
  const res = await api.put('/rag/settings', settings)
  return res.data
}