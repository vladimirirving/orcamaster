import axios from 'axios'

export const api = axios.create({ withCredentials: true })

let _accessToken = ''

export function setAccessToken(token: string) {
  _accessToken = token
}

api.interceptors.request.use((config) => {
  if (_accessToken) config.headers.Authorization = `Bearer ${_accessToken}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      error.config._retry = true
      try {
        const { data } = await axios.post('/auth/refresh', {}, { withCredentials: true })
        setAccessToken(data.access_token)
        error.config.headers.Authorization = `Bearer ${data.access_token}`
        return api(error.config)
      } catch {
        setAccessToken('')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
