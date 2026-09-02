import { Icon } from '../utils/icons'

export default function Header({
  token, family, user, userRole, screen, go, pendingCount, apiStatus, aiReady,
  onLogout, onCreateInvite, inviteCode
}) {
  return (
    <header>
      <button className="brand" onClick={() => go(userRole === 'parent' ? 'parent' : 'child')}>
        <b>슬쩍</b>
        <span>마음을 잇는 작은 질문</span>
      </button>

      {token && family && (
        <nav>
          {userRole === 'child' && (
            <button className={screen === 'child' ? 'on' : ''} onClick={() => go('child')}>
              마음 보내기
            </button>
          )}

          {userRole === 'parent' && (
            <button className={screen === 'parent' ? 'on' : ''} onClick={() => go('parent')}>
              오늘의 문답 {pendingCount > 0 && `(${pendingCount})`}
            </button>
          )}

          <button className={screen === 'library' ? 'on' : ''} onClick={() => go('library')}>
            지혜 서재
          </button>
        </nav>
      )}

      <div className="family">
        <div
          className="api-status"
          title={
            apiStatus === 'online'
              ? `서버 정상 (AI: ${aiReady ? '작동 중' : '로컬 모드'})`
              : '서버 연결 끊김 (백엔드 확인 필요)'
          }
        >
          <i className={`status-dot ${apiStatus === 'online' ? 'online' : 'offline'}`} />
          <span>{apiStatus === 'online' ? (aiReady ? 'AI ON' : 'API OK') : '서버 오프라인'}</span>
        </div>

        {user && (
          <div className="header-tools">
            <span>
              {family?.name || '가족'} <b>{user.name[0]}</b>
            </span>
            {inviteCode && <code>{inviteCode}</code>}
            <button className="header-action" onClick={onCreateInvite}>초대</button>
            <button className="header-logout" onClick={onLogout} title="로그아웃" aria-label="로그아웃">
              <Icon type="logout" />
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
