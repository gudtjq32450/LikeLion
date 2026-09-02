import { Icon } from '../utils/icons'

export default function LibraryPage({ library, formatDate, react, openRaw, setOpenRaw }) {
  return (
    <main className="page library">
      <div className="hero">
        <div>
          <div className="eyebrow">● 우리 가족 지혜 서재</div>
          <h1>우리가 나눈 지혜들</h1>
          <p className="lead">부모님의 경험과 온기가 담긴 답변들을 다시 읽고 간직할 수 있습니다.</p>
        </div>
        <div className="count">
          <Icon type="book" /><b>{library.length}</b><span>개의 이야기</span>
        </div>
      </div>

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
                <b>{item.author_name ? item.author_name[0] : '가'}</b>
                <div><strong>{item.author_name || '부모님'}</strong><span>가족의 지혜</span></div>
              </div>
              <div className="wisdom-foot">
                <div>
                  <button onClick={() => react(item.id, 'thanks')}>고마워요 {item.thanks_count > 0 && `(${item.thanks_count})`}</button>
                  <button onClick={() => react(item.id, 'moved')}>감동이에요 {item.moved_count > 0 && `(${item.moved_count})`}</button>
                </div>
                <button onClick={() => setOpenRaw(openRaw === item.id ? null : item.id)}>
                  {openRaw === item.id ? '원문 접기' : '원문 보기'}
                </button>
              </div>
              {openRaw === item.id && (
                <div className="raw"><b>원래 건넨 말씀</b><p>{item.raw_answer}</p></div>
              )}
            </article>
          ))
        )}
      </div>
    </main>
  )
}
