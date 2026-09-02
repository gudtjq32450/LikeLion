import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import './QuestionOptions.css'
import './FeatureUpdates.css'
import heroEnvelopeEyes from './assets/hero-envelope-eyes.png'
import heroLetter from './assets/hero-letter.gif'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const heroBackgrounds = [heroEnvelopeEyes, heroLetter]

const emotions = [
  ['지침', '😮‍💨'],
  ['불안', '😟'],
  ['기쁨', '😊'],
  ['외로움', '🥺'],
  ['설렘', '🥰'],
  ['슬픔', '😢'],
]

const formatDate = (dateString) => {
  if (!dateString) return ''
  const d = new Date(dateString)
  return new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' }).format(d)
}

function Icon({ type }) {
  const d = {
    arrow: 'M5 12h14m-5-5 5 5-5 5',
    back: 'm15 18-6-6 6-6',
    check: 'm5 12 4 4L19 6',
    mic: 'M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Zm-6 8a6 6 0 0 0 12 0m-6 6v4m-3 0h6',
    book: 'M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5V5.5Zm16 0A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z',
  }[type]
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={d} />
    </svg>
  )
}

export default function App() {
  // 인증 및 가족 정보
  const [token, setToken] = useState(() => localStorage.getItem('seuljjeock-token') || '')
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('seuljjeock-user')) || null
    } catch {
      return null
    }
  })
  const [family, setFamily] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('seuljjeock-family')) || null
    } catch {
      return null
    }
  })

  // 인증 모달 상태
  const [authMode, setAuthMode] = useState('login') // 'login', 'register', 'family_create', 'family_join'
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authName, setAuthName] = useState('')
  const [authRole, setAuthRole] = useState('child')
  const [inviteCodeInput, setInviteCodeInput] = useState('')
  const [familyNameInput, setFamilyNameInput] = useState('')
  const [inviteCode, setInviteCode] = useState('')

  // API 서버 상태 감시 인디케이터 ('checking' | 'online' | 'offline')
  const [apiStatus, setApiStatus] = useState('checking')
  const [aiReady, setAiReady] = useState(false)

  // 화면 탭 및 입력 상태
  const [screen, setScreen] = useState('child')
  const [emotion, setEmotion] = useState('지침')
  const [worry, setWorry] = useState('')
  const [mode, setMode] = useState('stealth')

  // 부모 화면용 상태
  const [currentDelivery, setCurrentDelivery] = useState(null)
  const [pendingDeliveries, setPendingDeliveries] = useState([])
  const [selectedQuestion, setSelectedQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [polished, setPolished] = useState('')

  // 서재 상태
  const [library, setLibrary] = useState([])
  const [openRaw, setOpenRaw] = useState(null)

  // 공통 UI 상태
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [recording, setRecording] = useState(false)
  const [heroIndex, setHeroIndex] = useState(0)
  const timer = useRef()

  const authHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }), [token])

  const go = (next) => {
    setScreen(next)
    setNotice('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const logout = () => {
    localStorage.removeItem('seuljjeock-token')
    localStorage.removeItem('seuljjeock-user')
    localStorage.removeItem('seuljjeock-family')
    setToken('')
    setUser(null)
    setFamily(null)
    setInviteCode('')
    setPendingDeliveries([])
    setLibrary([])
    setCurrentDelivery(null)
    setAuthMode('login')
    go('child')
  }

  const createInvite = async () => {
    setNotice('')
    try {
      const res = await fetch(`${API}/api/families/invites`, {
        method: 'POST',
        headers: authHeaders(),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '초대 코드 생성 실패')
      setInviteCode(data.invite_code)
      try {
        await navigator.clipboard.writeText(data.invite_code)
        setNotice(`초대 코드 ${data.invite_code}를 복사했습니다.`)
      } catch {
        setNotice(`초대 코드: ${data.invite_code}`)
      }
    } catch (err) {
      setNotice(err.message)
    }
  }

  // 1. API 헬스체크 루프 (5초마다 백엔드 감시)
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

  useEffect(() => {
    if (token) return undefined
    const interval = setInterval(() => {
      setHeroIndex((current) => (current + 1) % heroBackgrounds.length)
    }, 6500)
    return () => clearInterval(interval)
  }, [token])

  // 2. 미답변 질문 및 서재 목록 실시간 동기화
  const refreshData = useCallback(async () => {
    if (!token || !family?.id) return
    try {
      const qRes = await fetch(`${API}/api/questions/deliveries?family_id=${family.id}&status=pending`, {
        headers: authHeaders(),
      })
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

      const aRes = await fetch(`${API}/api/answers?family_id=${family.id}`, {
        headers: authHeaders(),
      })
      if (aRes.ok) {
        const answers = await aRes.json()
        setLibrary(answers)
      }
    } catch {
      setNotice('서버 데이터를 가져오는 중 오류가 발생했습니다.')
    }
  }, [authHeaders, family, token])

  useEffect(() => {
    if (token && family?.id) {
      // 서버 상태를 화면 진입 시 동기화해야 하므로 의도적으로 effect에서 갱신합니다.
      // oxlint-disable-next-line react-hooks/set-state-in-effect
      refreshData()
    }
  }, [family?.id, refreshData, screen, token])

  // 3. 인증 및 가족 처리
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
        if (!res.ok) throw new Error(data.detail || '로그인 실패')

        setToken(data.access_token)
        setUser(data.user)
        localStorage.setItem('seuljjeock-token', data.access_token)
        localStorage.setItem('seuljjeock-user', JSON.stringify(data.user))
        setNotice(`${data.user.name}님 환영합니다! 가족 그룹을 선택해 주세요.`)
        setAuthMode('family_join')
      } else if (authMode === 'register') {
        const res = await fetch(`${API}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: authEmail, password: authPassword, name: authName }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '회원가입 실패')
        setNotice('가입이 완료되었습니다. 로그인해 주세요.')
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
        localStorage.setItem('seuljjeock-family', JSON.stringify(data))
        setNotice(`'${data.name}' 가족이 생성되었습니다!`)
      } else if (authMode === 'family_join') {
        const res = await fetch(`${API}/api/families/join`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ invite_code: inviteCodeInput, role: authRole }),
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.detail || '가족 참여 실패')
        setFamily(data)
        localStorage.setItem('seuljjeock-family', JSON.stringify(data))
        setNotice(`'${data.name}' 가족에 합류했습니다!`)
      }
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 4. 자녀 질문 전송 (/api/questions/deliveries)
  async function transformAndSend() {
    if (!worry.trim()) return setNotice('마음에 걸리는 일을 한 줄만 들려주세요.')
    if (!family?.id) return setNotice('가족 그룹에 먼저 연결되어야 질문을 보낼 수 있습니다.')

    setLoading(true)
    setNotice('')
    try {
      const res = await fetch(`${API}/api/questions/deliveries`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          family_id: family.id,
          worry,
          emotion,
          mode,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '질문 전달 실패')

      setWorry('')
      setNotice('자녀 질문을 4개의 일상 질문 사이에 섞어 부모님께 조용히 보냈어요.')
      await refreshData()
      go('parent')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 5. 음성 시뮬레이션
  function record() {
    if (recording) {
      clearTimeout(timer.current)
      return setRecording(false)
    }
    setRecording(true)
    setNotice('부모님의 목소리를 듣고 있어요…')
    timer.current = setTimeout(() => {
      setRecording(false)
      setAnswer('나도 그때는 앞이 캄캄하고 막막했단다. 그래도 하루하루 버티다 보니 다 지나가더라.')
      setNotice('음성을 글로 옮겼어요.')
    }, 2200)
  }

  // 6. 부모 답변 AI 다듬기 (/api/answers/polish)
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
      if (!res.ok) throw new Error(data.detail || '답변 다듬기 실패')
      setPolished(data.polished)
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 7. 답변 최종 제출 (질문 answered 변경 및 서재 저장)
  async function saveAnswer() {
    if (!currentDelivery?.id) return setNotice('답변할 대상 질문이 없습니다.')
    setLoading(true)
    try {
      const res = await fetch(`${API}/api/answers/deliveries/${currentDelivery.id}`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          question: selectedQuestion,
          answer: answer,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '답변 저장 실패')

      setAnswer('')
      setPolished('')
      setNotice('부모님의 따뜻한 지혜가 서재에 등록되었습니다.')
      await refreshData()
      go('library')
    } catch (err) {
      setNotice(err.message)
    } finally {
      setLoading(false)
    }
  }

  // 8. 서재 공감 반응
  async function react(id, type) {
    try {
      const res = await fetch(`${API}/api/answers/${id}/reactions`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ reaction_type: type }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '반응 저장 실패')
      setLibrary(library.map((x) => (x.id === id ? { ...x, [`${type}_count`]: (x[`${type}_count`] || 0) + 1 } : x)))
    } catch (err) {
      setNotice(err.message)
    }
  }

  if (!token) {
    return (
      <div className="auth-landing">
        <div className="hero-backgrounds" aria-hidden="true">
          {heroBackgrounds.map((image, index) => (
            <div
              key={image}
              className={`hero-background ${heroIndex === index ? 'is-active' : ''}`}
              style={{ backgroundImage: `url(${image})` }}
            />
          ))}
        </div>
        <div className="hero-wash" aria-hidden="true" />

        <header className="landing-header">
          <button className="landing-brand" onClick={() => setHeroIndex((heroIndex + 1) % heroBackgrounds.length)}>
            <span>슬쩍</span>
            <small>마음을 잇는 작은 질문</small>
          </button>
          <div className={`landing-status ${apiStatus}`}>
            <i /> {apiStatus === 'online' ? (aiReady ? 'AI 연결됨' : '로컬 모드') : '연결 확인 중'}
          </div>
        </header>

        <main className="landing-content">
          <section className="landing-copy">
            <p className="landing-kicker">A LETTER BETWEEN US</p>
            <h1>
              말하기 어려운 마음을
              <br />
              질문 한 장에 담아요.
            </h1>
            <p>
              직접 꺼내기 어려웠던 이야기를 슬쩍 건네보세요.
              <br />
              가족의 경험이 다정한 답장이 되어 돌아옵니다.
            </p>
            <div className="hero-pagination" aria-label="배경 이미지 선택">
              {heroBackgrounds.map((_, index) => (
                <button
                  key={index}
                  className={heroIndex === index ? 'is-active' : ''}
                  onClick={() => setHeroIndex(index)}
                  aria-label={`${index + 1}번째 배경 보기`}
                />
              ))}
            </div>
          </section>

          <section className="auth-card">
            <div className="auth-card-heading">
              <span>{authMode === 'login' ? '다시 만나 반가워요' : '우리 가족의 첫 페이지'}</span>
              <h2>{authMode === 'login' ? '로그인' : '회원가입'}</h2>
              <p>{authMode === 'login' ? '가족에게 도착한 마음을 확인해 보세요.' : '가볍게 시작하고, 천천히 마음을 나눠요.'}</p>
            </div>

            <form className="auth-form" onSubmit={handleAuthSubmit}>
              {authMode === 'register' && (
                <label>
                  <span>이름 또는 호칭</span>
                  <input
                    type="text"
                    placeholder="예: 딸, 아빠"
                    value={authName}
                    onChange={(e) => setAuthName(e.target.value)}
                    required
                  />
                </label>
              )}
              <label>
                <span>이메일</span>
                <input
                  type="email"
                  placeholder="family@example.com"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                />
              </label>
              <label>
                <span>비밀번호</span>
                <input
                  type="password"
                  placeholder="4자 이상 입력해 주세요"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  required
                />
              </label>

              {notice && <p className="auth-notice">{notice}</p>}
              <button className="auth-submit" type="submit" disabled={loading}>
                {loading ? '마음을 여는 중…' : authMode === 'login' ? '로그인하기' : '계정 만들기'}
                {!loading && <Icon type="arrow" />}
              </button>
            </form>

            <div className="auth-switch">
              <span>{authMode === 'login' ? '아직 계정이 없나요?' : '이미 계정이 있나요?'}</span>
              <button onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
                {authMode === 'login' ? '회원가입' : '로그인'}
              </button>
            </div>
          </section>
        </main>
      </div>
    )
  }

  if (!family) {
    return (
      <div className="family-onboarding">
        <div className="onboarding-orb orb-one" />
        <div className="onboarding-orb orb-two" />
        <header className="onboarding-header">
          <b>슬쩍</b>
          <button onClick={logout}>로그아웃</button>
        </header>
        <main className="onboarding-card">
          <span className="onboarding-step">WELCOME, {user?.name}</span>
          <h1>{authMode === 'family_create' ? '새 가족의 문을 열어요' : '가족의 초대를 받았나요?'}</h1>
          <p>한 가족으로 연결되면 질문과 답장을 안전하게 나눌 수 있어요.</p>

          <form className="auth-form onboarding-form" onSubmit={handleAuthSubmit}>
            {authMode === 'family_create' ? (
              <label>
                <span>가족 이름</span>
                <input
                  type="text"
                  placeholder="예: 김가네 마음 우체국"
                  value={familyNameInput}
                  onChange={(e) => setFamilyNameInput(e.target.value)}
                  required
                />
              </label>
            ) : (
              <label>
                <span>초대 코드</span>
                <input
                  type="text"
                  placeholder="8자리 코드를 입력해 주세요"
                  value={inviteCodeInput}
                  onChange={(e) => setInviteCodeInput(e.target.value.toUpperCase())}
                  required
                />
              </label>
            )}

            <fieldset className="role-picker">
              <legend>나의 역할</legend>
              <label className={authRole === 'child' ? 'selected' : ''}>
                <input type="radio" name="role" value="child" checked={authRole === 'child'} onChange={() => setAuthRole('child')} />
                <span>자녀</span>
                <small>마음을 질문으로 보내요</small>
              </label>
              <label className={authRole === 'parent' ? 'selected' : ''}>
                <input type="radio" name="role" value="parent" checked={authRole === 'parent'} onChange={() => setAuthRole('parent')} />
                <span>부모</span>
                <small>경험을 답장으로 남겨요</small>
              </label>
            </fieldset>

            {notice && <p className="auth-notice">{notice}</p>}
            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? '연결하는 중…' : authMode === 'family_create' ? '가족 만들기' : '가족과 연결하기'}
              {!loading && <Icon type="arrow" />}
            </button>
          </form>

          <button
            className="onboarding-switch"
            onClick={() => setAuthMode(authMode === 'family_join' ? 'family_create' : 'family_join')}
          >
            {authMode === 'family_join' ? '초대 코드가 없어요 · 새 가족 만들기' : '이미 초대 코드가 있어요 · 참여하기'}
          </button>
        </main>
      </div>
    )
  }

  return (
    <div className="app">
      {/* 헤더 네비게이션 */}
      <header>
        <button className="brand" onClick={() => go('child')}>
          <b>슬쩍</b>
          <span>마음을 잇는 작은 질문</span>
        </button>
        <nav>
          <button className={screen === 'child' ? 'on' : ''} onClick={() => go('child')}>
            마음 보내기
          </button>
          <button className={screen === 'parent' ? 'on' : ''} onClick={() => go('parent')}>
            오늘의 문답 {pendingDeliveries.length > 0 && `(${pendingDeliveries.length})`}
          </button>
          <button className={screen === 'library' ? 'on' : ''} onClick={() => go('library')}>
            지혜 서재
          </button>
        </nav>
        <div className="family">
          {/* API 상태 표시 인디케이터 (초록불/빨간불) */}
          <div
            className="api-status"
            title={
              apiStatus === 'online'
                ? `API 연결됨 (AI: ${aiReady ? '활성화' : '로컬 모드'})`
                : 'API 연결 끊김 (백엔드 서버 확인 필요)'
            }
          >
            <i className={`status-dot ${apiStatus === 'online' ? 'online' : 'offline'}`} />
            <span>{apiStatus === 'online' ? (aiReady ? 'AI ON' : 'API OK') : '서버 오프라인'}</span>
          </div>

          {user ? (
            <span>
              {family?.name || '가족 미참여'} <b>{user.name[0]}</b>
            </span>
          ) : (
            <button
              onClick={() => setAuthMode('login')}
              style={{ border: 0, background: 'var(--terra)', color: '#fff', padding: '6px 12px', borderRadius: 4 }}
            >
              로그인
            </button>
          )}
        </div>
      </header>

      {token && family && (
        <div className="session-bar">
          <span>
            <b>{family.name}</b> · {user?.name}
          </span>
          {inviteCode && <code>{inviteCode}</code>}
          <button onClick={createInvite}>초대 코드 만들기</button>
          <button onClick={logout}>로그아웃</button>
        </div>
      )}

      {/* 인증 및 가족 관리 모달 */}
      {(!token || !family) && (
        <div className="paper" style={{ maxWidth: 450, margin: '40px auto', padding: 30 }}>
          <h2 style={{ fontFamily: 'var(--serif)', marginBottom: 15, color: 'var(--ink)' }}>
            {!token
              ? authMode === 'login'
                ? '로그인'
                : '회원가입'
              : authMode === 'family_create'
                ? '새 가족 만들기'
                : '가족 초대 코드 입력'}
          </h2>

          <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {!token && authMode === 'register' && (
              <input
                type="text"
                placeholder="이름 또는 호칭 (예: 딸, 아빠)"
                value={authName}
                onChange={(e) => setAuthName(e.target.value)}
                required
                style={{ padding: 10, border: '1px solid var(--line)' }}
              />
            )}
            {!token && (
              <>
                <input
                  type="email"
                  placeholder="이메일 주소"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  required
                  style={{ padding: 10, border: '1px solid var(--line)' }}
                />
                <input
                  type="password"
                  placeholder="비밀번호"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  required
                  style={{ padding: 10, border: '1px solid var(--line)' }}
                />
              </>
            )}

            {token && authMode === 'family_create' && (
              <input
                type="text"
                placeholder="가족 이름 (예: 김가네)"
                value={familyNameInput}
                onChange={(e) => setFamilyNameInput(e.target.value)}
                required
                style={{ padding: 10, border: '1px solid var(--line)' }}
              />
            )}

            {token && authMode === 'family_join' && (
              <input
                type="text"
                placeholder="8자리 초대 코드"
                value={inviteCodeInput}
                onChange={(e) => setInviteCodeInput(e.target.value)}
                required
                style={{ padding: 10, border: '1px solid var(--line)' }}
              />
            )}

            {token && (
              <div style={{ display: 'flex', gap: 15, fontSize: 13 }}>
                <label>
                  <input
                    type="radio"
                    name="role"
                    value="child"
                    checked={authRole === 'child'}
                    onChange={() => setAuthRole('child')}
                  />{' '}
                  자녀
                </label>
                <label>
                  <input
                    type="radio"
                    name="role"
                    value="parent"
                    checked={authRole === 'parent'}
                    onChange={() => setAuthRole('parent')}
                  />{' '}
                  부모
                </label>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                padding: 12,
                background: 'var(--terra)',
                color: '#fff',
                border: 0,
                borderRadius: 4,
                fontWeight: 'bold',
              }}
            >
              {loading ? '처리 중...' : '확인'}
            </button>
          </form>

          <div style={{ marginTop: 15, display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
            {!token ? (
              <button
                onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
                style={{ border: 0, background: 'none', color: 'var(--muted)' }}
              >
                {authMode === 'login' ? '회원가입하기' : '이미 계정이 있으신가요? 로그인'}
              </button>
            ) : (
              <button
                onClick={() => setAuthMode(authMode === 'family_join' ? 'family_create' : 'family_join')}
                style={{ border: 0, background: 'none', color: 'var(--muted)' }}
              >
                {authMode === 'family_join' ? '가족 만들기' : '초대 코드로 참여하기'}
              </button>
            )}
          </div>
        </div>
      )}

      {notice && <p className="notice">{notice}</p>}

      {/* 1. 자녀 화면 (마음 보내기) */}
      {screen === 'child' && (
        <main className="page child">
          <div className="eyebrow">마음 전달</div>
          <h1>
            마음에 걸리는 일을
            <br />
            슬쩍 꺼내보세요
          </h1>
          <p className="lead">
            자녀의 직접적인 고민 내용은 부모님께 노출되지 않습니다.
            <br />
            AI가 부모님의 과거 회고 질문으로 바꾸어 다른 일상 질문 4개와 함께 전달합니다.
          </p>

          <div className="paper">
            <div className="step">
              <span>01</span>
              <div>
                <h2>지금 마음의 날씨</h2>
                <p>가장 가까운 감정을 골라주세요</p>
              </div>
            </div>
            <div className="emotions">
              {emotions.map(([label, icon]) => (
                <button
                  key={label}
                  className={emotion === label ? 'selected' : ''}
                  onClick={() => setEmotion(label)}
                >
                  <i>{icon}</i>
                  <span>{label}</span>
                </button>
              ))}
            </div>

            <hr />

            <div className="step">
              <span>02</span>
              <div>
                <h2>속마음 적어보기</h2>
                <p>부모님께 직접 말하기 힘든 고민을 적어주세요</p>
              </div>
            </div>
            <label className="field">
              <textarea
                placeholder="예: 취업 준비가 길어져서 자꾸 포기하고 싶어져요. 노력해도 안 되는 것 같아 막막해요."
                value={worry}
                onChange={(e) => setWorry(e.target.value)}
              />
              <small>{worry.length}자</small>
            </label>

            <hr />

            <div className="step">
              <span>03</span>
              <div>
                <h2>전달 방식</h2>
                <p>자녀의 원래 고민은 저장되지 않고 질문 피드로만 변환됩니다</p>
              </div>
            </div>
            <div className="modes">
              <button
                className={mode === 'stealth' ? 'selected' : ''}
                onClick={() => setMode('stealth')}
              >
                <i />
                <div>
                  <b>
                    익명 질문 묶음 <em>추천</em>
                  </b>
                  <p>4개의 가벼운 일상 질문 속에 자녀의 핵심 질문 1개를 숨겨서 전달합니다.</p>
                </div>
              </button>
              <button
                className={mode === 'direct' ? 'selected' : ''}
                onClick={() => setMode('direct')}
              >
                <i />
                <div>
                  <b>단독 질문</b>
                  <p>정제된 회고 질문 1개만 부모님께 전달합니다.</p>
                </div>
              </button>
            </div>

            <button className="action" disabled={loading} onClick={transformAndSend}>
              {loading ? <i></i> : '질문 배달하기'}
              {!loading && <Icon type="arrow" />}
            </button>
            <p className="privacy">자녀의 원문 고민은 AI 변환 즉시 삭제되며 DB에 저장되지 않습니다.</p>
          </div>
        </main>
      )}

      {/* 2. 부모 화면 (오늘의 문답) */}
      {screen === 'parent' && (
        <main className="page parent">
          <button className="back" onClick={() => go('child')}>
            <Icon type="back" /> 자녀 모드로 돌아가기
          </button>
          <div className="hero">
            <div>
              <div className="eyebrow">오늘의 문답</div>
              <h1>
                자녀에게서 도착한
                <br />
                질문 묶음
              </h1>
              <p className="lead">
                가족의 마음이 담긴 질문들입니다. 편하게 마음에 드는 질문을 골라 짧게 경험을 들려주세요.
              </p>
            </div>
            <div className="date">
              <span>DATE</span>
              <b>{new Date().getDate()}</b>
              <small>{new Date().getMonth() + 1}월</small>
            </div>
          </div>

          {pendingDeliveries.length === 0 ? (
            <div className="paper" style={{ textAlign: 'center', padding: '60px 20px' }}>
              <p style={{ color: 'var(--muted)', fontSize: 15 }}>현재 도착한 미답변 질문이 없습니다.</p>
              <button
                className="action"
                style={{ width: 220, margin: '20px auto 0' }}
                onClick={() => go('child')}
              >
                새 질문 보내보기
              </button>
            </div>
          ) : (
            <div className="paper">
              <div className="step">
                <span>01</span>
                <div>
                  <h2>답변할 질문 선택</h2>
                  <p>5개의 질문 중 이야기해 주고 싶은 질문을 선택해 주세요</p>
                </div>
              </div>
              <div style={{ display: 'grid', gap: 10, marginBottom: 25 }}>
                {currentDelivery?.questions?.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedQuestion(q)}
                    style={{
                      padding: '14px 16px',
                      textAlign: 'left',
                      border: selectedQuestion === q ? '2px solid var(--terra)' : '1px solid var(--line)',
                      background: selectedQuestion === q ? '#fdf5ef' : '#fffcf8',
                      borderRadius: 4,
                      fontSize: 14,
                      fontFamily: 'var(--serif)',
                    }}
                  >
                    {idx + 1}. {q}
                  </button>
                ))}
              </div>

              <div className="question">
                <div>
                  <b>선택된 질문</b>
                  <em>{currentDelivery?.emotion}</em>
                </div>
                <blockquote>{selectedQuestion}</blockquote>
              </div>

              <div className="answer">
                <div className="answer-head">
                  <h2>나의 경험 들려주기</h2>
                  <span>텍스트 또는 음성</span>
                </div>

                <div className={`recorder ${recording ? 'live' : ''}`}>
                  <button onClick={record}>
                    <Icon type="mic" />
                  </button>
                  <div>
                    <b>음성으로 들려주기</b>
                    <small>{recording ? '음성을 듣고 있습니다...' : '마이크 버튼을 눌러 말씀해 보세요'}</small>
                  </div>
                  {recording && (
                    <div className="wave">
                      <i />
                      <i />
                      <i />
                    </div>
                  )}
                </div>

                <div className="or">또는 직접 입력</div>

                <div className="field">
                  <textarea
                    placeholder="그때를 돌이켜보면 어떤 마음이었는지 편하게 적어주세요."
                    value={answer}
                    onChange={(e) => setAnswer(e.target.value)}
                  />
                </div>

                <button
                  className="action"
                  disabled={loading || !answer.trim()}
                  onClick={polish}
                  style={{ marginTop: 15 }}
                >
                  {loading ? <i></i> : 'AI로 말투 다듬기'}
                </button>

                {polished && (
                  <div className="polished">
                    <div>
                      <span>자녀에게 전달될 다듬어진 문장</span>
                    </div>
                    <p>{polished}</p>
                    <div className="actions">
                      <button onClick={() => setPolished('')}>다시 쓰기</button>
                      <button onClick={saveAnswer} disabled={loading}>
                        이 답변으로 지혜 남기기
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      )}

      {/* 3. 지혜 서재 화면 */}
      {screen === 'library' && (
        <main className="page library">
          <div className="eyebrow">가족 서재</div>
          <h1>우리가 나눈 지혜들</h1>
          <p className="lead">부모님의 경험과 온기가 담긴 답변들을 다시 읽고 간직할 수 있습니다.</p>

          <div className="wisdom-list" style={{ marginTop: 35 }}>
            {library.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--muted)', padding: 40 }}>아직 등록된 지혜 답변이 없습니다.</p>
            ) : (
              library.map((item) => (
                <article key={item.id} className="wisdom">
                  <div className="wisdom-top">
                    <span>{item.emotion || '따뜻함'}</span>
                    <time>{formatDate(item.created_at)}</time>
                  </div>
                  <small>질문: {item.question}</small>
                  <blockquote>{item.polished_answer}</blockquote>

                  <div className="author">
                    <b>{item.author_name ? item.author_name[0] : '부'}</b>
                    <div>
                      <strong>{item.author_name || '부모님'}</strong>
                      <span>가족의 지혜</span>
                    </div>
                  </div>

                  <div className="wisdom-foot">
                    <div>
                      <button onClick={() => react(item.id, 'thanks')}>
                        고마워요 {item.thanks_count > 0 && `(${item.thanks_count})`}
                      </button>
                      <button onClick={() => react(item.id, 'moved')}>
                        감동이에요 {item.moved_count > 0 && `(${item.moved_count})`}
                      </button>
                    </div>
                    <button onClick={() => setOpenRaw(openRaw === item.id ? null : item.id)}>
                      {openRaw === item.id ? '원문 접기' : '부모님 말씀 원문 보기'}
                    </button>
                  </div>

                  {openRaw === item.id && (
                    <div className="raw">
                      <b>부모님의 원래 답변</b>
                      <p>{item.raw_answer}</p>
                    </div>
                  )}
                </article>
              ))
            )}
          </div>
        </main>
      )}

      <footer>
        <b>슬쩍</b>
        <p>자녀의 조용한 고민과 부모의 지나온 삶을 잇습니다.</p>
        <small>© 2026 SEUL-JJEOCK. All rights reserved.</small>
      </footer>
    </div>
  )
}
