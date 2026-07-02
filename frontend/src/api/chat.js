import api from './index'

// 세션 목록
export const fetchSessions = async () => {
  const res = await api.get('/session/')
  return res.data
}

// 새 세션 생성
export const createSession = async (title, useKnowledge = false) => {
  const res = await api.post('/session/', {
    title        : title,
    use_knowledge: useKnowledge
  })
  return res.data
}

// 세션 삭제
export const deleteSession = async (id) => {
  await api.delete(`/session/${id}`)
}

// 특정 세션 메시지 목록
export const fetchMessages = async (sessionId) => {
  const res = await api.get(`/session/${sessionId}/messages`)
  return res.data
}

/**
 * SSE 스트리밍 채팅
 * - onToken  : 토큰 수신 콜백
 * - onStatus : 상태 메시지 콜백 (툴 실행중 등)
 * - onClear  : 클리어 콜백
 * - onDone   : 완료 콜백
 * - onError  : 에러 콜백
 */
export const streamChat = (sessionId, message, mode = 'auto', model = '', { onToken, onStatus, onClear, onDone, onError }) => {
  // fetch로 SSE POST 요청
  fetch('http://localhost:8888/api/chat/', {
    method : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body   : JSON.stringify({ session_id: sessionId, message, mode, model })
  }).then(async res => {
    const reader  = res.body.getReader()
    const decoder = new TextDecoder()
    
    // eslint-disable-next-line no-constant-condition
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // SSE 파싱: "data: {...}\n\n" 형식
      const lines = decoder.decode(value).split('\n')
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const json = JSON.parse(line.slice(6))
          if      (json.type === 'token' ) onToken(json.content)
          else if (json.type === 'status') onStatus(json.content)
          else if (json.type === 'clear' ) onClear() 
          else if (json.type === 'done'  ) onDone()
          else if (json.type === 'error' ) onError(json.content)
        } catch(error) {console.error(error);}
      }
    }
  }).catch(onError)
}

export const fetchTools = async () => {
  const res = await api.get('/tools/')
  return res.data   // [{ name, description, full_description }]
}

// 세션 설정 수정
export const updateSession = async (id, data) => {
  const res = await api.patch(`/session/${id}`, data)
  return res.data
}

// 세션 컨텍스트 전체 조회
export const fetchSessionContext = async (id) => {
  const res = await api.get(`/session/${id}/context`)
  return res.data
}

// Ollama 모델 목록 조회
export const fetchOllamaModels = async () => {
  const res = await api.get('/models/')
  return res.data
}