import axios from 'axios'

const api = axios.create({
  baseURL: process.env.VUE_APP_API_URL
    ? process.env.VUE_APP_API_URL + '/api'
    : '/api',
  timeout: 60000
})

export default api
