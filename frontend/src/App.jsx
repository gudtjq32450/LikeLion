import { useEffect, useRef, useState } from 'react'
import './App.css'
import './QuestionOptions.css'
import './FeatureUpdates.css'

import Header from './components/Header'
import AuthModal from './components/AuthModal'
import ChildPage from './components/ChildPage'
import ParentPage from './components/ParentPage'
import LibraryPage from './components/LibraryPage'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const formatDate = (dateString) => {
  if (!dateString) return ''
  const d = new Date(dateString)
  return new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' }).format(d)
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('seuljjeock-token') || '')
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('seuljjeock-user')) || null } catch { return null }
  })
  const [family, setFamily] = useState(() => {
    try { return JSON.parse(localStorage.getItem('seuljjeock-family')) || null } catch { return null }
  })
  const [userRole, setUserRole] = useState(() => localStorage.getItem('seuljjeock-role') || 'child')

  const [authMode, setAuthMode] = useState('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authName, setAuthName] = useState('')
  const [authRole, setAuthRole] = useState('child')
  const [authSubRole, setAuthSubRole] = useState('딸')
  const [inviteCodeInput, setInviteCodeInput] = useState('')
  const [familyNameInput, setFamilyNameInput] = useState('')

  const [apiStatus, setApiStatus] = useState('checking')
  const [aiReady, setAiReady] = useState(false)
  const [screen, setScreen] = useState(() => (userRole === 'parent' ? 'parent' : 'child'))
  const [emotion, setEmotion] = useState('지침')
  const [worry, setWorry] = useState('')
  const [mode, setMode] = useState('stealth')

  const [currentDelivery, setCurrentDelivery] = useState(null)
  const [pendingDeliveries, setPendingDeliveries] = useState([])
  const [selectedQuestion, setSelectedQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [polished, setPolished] = useState('')
  const [library, setLibrary] = useState([])
  const [openRaw, setOpenRaw] = useState(null)

  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [recording, setRecording] = useState(false)
  const timer = useRef()

  const authHeaders = () => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  })

  const go = (next) => {
    setScreen(next)
    setNotice('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${API}/api/health`, { method: 'GET' })
        if (res.ok) {
          const data = await res.json()
          setApiStatus('online')
          setAiReady(Boolean(data.ai))
        } else {
          setApiStatus('offline')
          setAiReady(false)
        }
      } catch {
        setApiStatus('offline')
        setAiReady(false)
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  const refreshData = async () => {
    if (!token || !family?.id) return
    try {
      const qRes = await fetch(`${API}/api/questions/deliveries?family_id=${family.id}&status=pending`, { headers: authHeaders() })
      if (qRes.ok) {
        const deliveries = await qRes.json()
        setPendingDeliveries(deliveries)
        if (deliveries.length > 0) {
          setCurrentDelivery(deliveries[0])
          setSelectedQuestion(deliveries[0].questions[0] || deliveries[0].target_question)
        } else {
          setCurrentDelivery(null)
          setSelectedQuestion('')
        }
      }
      const aRes = await fetch(`${API}/api/answers?family_id=${family.id}`, { headers: authHeaders() })
      if (aRes.ok) {
        const answers = await aRes.json()
        setLibrary(answers)
      }
    } catch {}
  }

  useEffect(() => {
    if (token && family?.id) refreshData()
  }, [token, family?.id, screen])

  const handleRoleChange = (role) => {
    setAuthRole(role)
    if (role === 'child') {
      setAuthSubRole('딸')
      if (!authName || ['아빠', '엄마'].includes(authName)) setAuthName('딸')
    } else {
      setAuthSubRole('아빠')
      if (!authName || ['아들', '딸'].includes(authName)) setAuthName('아빠')
    }
  }

  const handleSubRoleChange = (sub) => {
    setAuthSubRole(sub)
    setAuthName(sub)
  }

  const handleAuthSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setNotice('')
    try {
      if (authMode === 'login') {
        const res = await fetch(`${API}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authEmail, password: authPassword }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '로그인에 실패했습니다.')
        setToken(data.access_token)
        setUser(data.user)
        localStorage.setItem('seuljjeock-token', data.access_token)
        localStorage.setItem('seuljjeock-user', JSON.stringify(data.user))
        setNotice(`${data.user.name}님 환영합니다! 가족 그룹을 연결해 주세요.`)
        setAuthMode('family_join')
      } else if (authMode === 'register') {
        const displayName = authName.trim() || authSubRole
        const res = await fetch(`${API}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authEmail, password: authPassword, name: displayName }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '회원가입에 실패했습니다.')
        setNotice('가입이 완료되었습니다. 방금 만든 정보로 로그인해 주세요.')
        setAuthMode('login')
      } else if (authMode === 'family_create') {
        const res = await fetch(`${API}/api/families`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ name: familyNameInput, role: authRole }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '가족 생성 실패')
        setFamily(data)
        setUserRole(authRole)
        localStorage.setItem('seuljjeock-family', JSON.stringify(data))
        localStorage.setItem('seuljjeock-role', authRole)
        setNotice(`'${data.name}' 가족이 연결되었습니다!`)
        go(authRole === 'parent' ? 'parent' : 'child')
      } else if (authMode === 'family_join') {
        const res = await fetch(`${API}/api/families/join`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ invite_code: inviteCodeInput, role: authRole }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '가족 참여 실패')
        setFamily(data)
        setUserRole(authRole)
        localStorage.setItem('seuljjeock-family', JSON.stringify(data))
        localStorage.setItem('seuljjeock-role', authRole)
        setNotice(`'${data.name}' 가족에 참여하셨습니다!`)
        go(authRole === 'parent' ? 'parent' : 'child')
      }
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('seuljjeock-token')
    localStorage.removeItem('seuljjeock-user')
    localStorage.removeItem('seuljjeock-family')
    localStorage.removeItem('seuljjeock-role')
    setToken('')
    setUser(null)
    setFamily(null)
    setUserRole('child')
    setAuthMode('login')
    setNotice('로그아웃되었습니다.')
  }

  async function transformAndSend() {
    if (!worry.trim()) return setNotice('마음에 걸리는 일을 한 줄만 들려주세요.')
    if (!family?.id) return setNotice('가족 그룹에 먼저 연결되어야 질문을 전송할 수 있습니다.')
    setLoading(true)
    setNotice('')
    try {
      const res = await fetch(`${API}/api/questions/deliveries`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ family_id: family.id, worry, emotion, mode }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '질문 전달 실패')
      setWorry('')
      setNotice('부모님이 부담 느끼지 않도록 4개의 일상 질문 사이에 섞어 조용히 보냈어요.')
      await refreshData()
      go('library')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  function record() {
    if (recording) { clearTimeout(timer.current); return setRecording(false) }
    setRecording(true)
    setNotice('목소리를 듣고 있어요…')
    timer.current = setTimeout(() => {
      setRecording(false)
      setAnswer('나도 그때는 앞이 캄캄하고 막막했단다. 그래도 하루하루 버티다 보니 다 지나가더라.')
      setNotice('음성을 글로 옮겼어요.')
    }, 2200)
  }

  async function polish() {
    if (!answer.trim()) return setNotice('짧게라도 경험을 들려주세요.')
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/answers/polish`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ answer, question: selectedQuestion }),
      })
      const data = await res.json()
      setPolished(data.polished)
    } catch {
      setPolished('나도 그 시절에는 두려웠단다. 하지만 그 시간이 지나고 보니 다음 길을 찾는 소중한 힘이 되었어.')
    } finally {
      setLoading(false)
    }
  }

  async function saveAnswer() {
    if (!currentDelivery?.id) return setNotice('답변할 대상 질문이 없습니다.')
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/answers/deliveries/${currentDelivery.id}`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ question: selectedQuestion, answer }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '답변 저장 실패')
      setAnswer('')
      setPolished('')
      setNotice('부모님의 소중한 경험이 가족 서재에 기록되었습니다.')
      await refreshData()
      go('library')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function react(id, type) {
    try {
      await fetch(`${API}/api/answers/${id}/reactions`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ reaction_type: type }),
      })
      setLibrary(library.map((x) => (x.id === id ? { ...x, [`${type}_count`]: (x[`${type}_count`] || 0) + 1 } : x)))
    } catch {}
  }

  return (
    <div className="app">
      <Header
        token={token} family={family} user={user} userRole={userRole} screen={screen}
        go={go} pendingCount={pendingDeliveries.length} apiStatus={apiStatus} aiReady={aiReady} onLogout={handleLogout}
      />

      {(!token || !family) && (
        <AuthModal
          token={token} authMode={authMode} setAuthMode={setAuthMode} authRole={authRole}
          handleRoleChange={handleRoleChange} authSubRole={authSubRole} handleSubRoleChange={handleSubRoleChange}
          authName={authName} setAuthName={setAuthName} authEmail={authEmail} setAuthEmail={setAuthEmail}
          authPassword={authPassword} setAuthPassword={setAuthPassword}
          familyNameInput={familyNameInput} setFamilyNameInput={setFamilyNameInput}
          inviteCodeInput={inviteCodeInput} setInviteCodeInput={setInviteCodeInput}
          handleAuthSubmit={handleAuthSubmit} loading={loading}
        />
      )}

      {notice && <p className="notice">{notice}</p>}

      {token && family && userRole === 'child' && screen === 'child' && (
        <ChildPage
          emotion={emotion} setEmotion={setEmotion} worry={worry} setWorry={setWorry}
          mode={mode} setMode={setMode} transformAndSend={transformAndSend} loading={loading}
        />
      )}

      {token && family && userRole === 'parent' && screen === 'parent' && (
        <ParentPage
          pendingDeliveries={pendingDeliveries} currentDelivery={currentDelivery}
          selectedQuestion={selectedQuestion} setSelectedQuestion={setSelectedQuestion}
          recording={recording} record={record} answer={answer} setAnswer={setAnswer}
          polished={polished} setPolished={setPolished} polish={polish} saveAnswer={saveAnswer}
          loading={loading} go={go}
        />
      )}

      {token && family && screen === 'library' && (
        <LibraryPage library={library} formatDate={formatDate} react={react} openRaw={openRaw} setOpenRaw={setOpenRaw} />
      )}

      <footer>
        <b>슬쩍</b>
        <p>자녀의 조용한 고민과 부모의 지나온 삶을 잇습니다.</p>
        <small>© 2026 SEUL-JJEOCK. All rights reserved.</small>
      </footer>
    </div>
  )
}
