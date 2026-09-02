import { Icon } from '../utils/icons'

export default function ParentPage({
  pendingDeliveries, currentDelivery, chooseDelivery, selectedQuestion, setSelectedQuestion,
  recording, record, answer, setAnswer, polished, setPolished, polish, saveAnswer,
  recommendationReason, setRecommendationReason, answerTone, setAnswerTone, toneOptions,
  loading
}) {
  const delayedCount = pendingDeliveries.filter((delivery) => delivery.mode === 'stealth' && delivery.should_notify).length
  return (
    <main className="page parent">
      <div className="hero">
        <div>
          <div className="eyebrow">● 오늘의 인생 문답</div>
          <h1>{currentDelivery?.mode === 'direct' ? '가족에게서 도착한' : '자녀에게서 도착한'}<br />{currentDelivery?.mode === 'direct' ? '단독 질문' : '질문 묶음'}</h1>
          <p className="lead">가족의 마음이 담긴 질문입니다. 지나온 경험을 편하게 들려주세요.</p>
        </div>
        <div className="date">
          <span>DATE</span><b>{new Date().getDate()}</b><small>{new Date().getMonth() + 1}월</small>
        </div>
      </div>

      {pendingDeliveries.length === 0 ? (
        <div className="paper" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <p style={{ color: 'var(--muted)', fontSize: 15 }}>현재 도착한 미답변 질문이 없습니다.</p>
          <p style={{ color: '#b0a197', fontSize: 13, marginTop: 6 }}>자녀가 마음을 담아 새 질문을 보내면 여기에 표시됩니다.</p>
        </div>
      ) : (
        <>
        {delayedCount > 0 && (
          <div className="answer-nudge" role="status">
            <b>답변을 기다리는 질문이 있어요</b>
            <p>하루 넘게 기다린 질문 묶음이 {delayedCount}개 있습니다. 여유가 될 때 경험을 들려주세요.</p>
          </div>
        )}
        <div className="delivery-inbox">
          <div className="delivery-inbox-head"><b>도착한 문답</b><span>{pendingDeliveries.length}개</span></div>
          <div>
            {pendingDeliveries.map((delivery) => (
              <button key={delivery.id} className={currentDelivery?.id === delivery.id ? 'selected' : ''} onClick={() => chooseDelivery(delivery)}>
                <span>{delivery.mode === 'direct' ? '단독 질문' : '질문 묶음'}</span>
                <b>{delivery.mode === 'direct' ? delivery.target_question : `${delivery.questions.length}개의 질문`}</b>
                <small>{delivery.should_notify ? '답변을 기다리고 있어요' : '새로 도착했어요'}</small>
              </button>
            ))}
          </div>
        </div>
        <div className="paper parent-answer-paper">
          <div className="step">
            <span>01</span>
            <div><h2>답변할 질문 선택</h2><p>5개의 질문 중 이야기해 주고 싶은 질문을 선택해 주세요</p></div>
          </div>
          <div style={{ display: 'grid', gap: 10, marginBottom: 25 }}>
            {currentDelivery?.questions?.map((q, idx) => (
              <button key={idx} onClick={() => setSelectedQuestion(q)} style={{ padding: '14px 16px', textAlign: 'left', border: selectedQuestion === q ? '2px solid var(--terra)' : '1px solid var(--line)', background: selectedQuestion === q ? '#fdf5ef' : '#fffcf8', borderRadius: 4, fontSize: 14, fontFamily: 'var(--serif)', cursor: 'pointer' }}>
                {idx + 1}. {q}
              </button>
            ))}
          </div>

          <div className="question">
            <div><b>선택된 질문</b><em>{currentDelivery?.emotion}</em></div>
            <blockquote>{selectedQuestion}</blockquote>
          </div>

          <div className="answer">
            <div className="answer-head"><h2>나의 경험 들려주기</h2><span>텍스트 또는 음성</span></div>
            <div className="tone-picker">
              <div><b>전하고 싶은 말투</b><span>원래 의도에 가장 가까운 문체를 골라주세요.</span></div>
              <div>
                {toneOptions.map((tone) => (
                  <button
                    type="button"
                    key={tone.value}
                    className={answerTone === tone.value ? 'selected' : ''}
                    onClick={() => {
                      setAnswerTone(tone.value)
                      setPolished('')
                      setRecommendationReason('')
                    }}
                  >
                    <b>{tone.title}</b><small>{tone.description}</small>
                  </button>
                ))}
              </div>
            </div>
            <div className={`recorder ${recording ? 'live' : ''}`}>
              <button onClick={record}><Icon type="mic" /></button>
              <div><b>음성으로 들려주기</b><small>{recording ? '음성을 듣고 있습니다...' : '마이크 버튼을 눌러 말씀해 보세요'}</small></div>
              {recording && <div className="wave"><i /><i /><i /></div>}
            </div>

            <div className="or">또는 직접 입력</div>
            <div className="field">
              <textarea placeholder="그때를 돌이켜보면 어떤 마음이었는지 편하게 적어주세요." value={answer} onChange={(e) => { setAnswer(e.target.value); setPolished(''); setRecommendationReason('') }} />
            </div>

            <button className="action" disabled={loading || !answer.trim()} onClick={polish} style={{ marginTop: 15 }}>
              {loading ? <i /> : 'AI로 말투 다듬기'}
            </button>

            {polished && (
              <div className="polished">
                <div><span>자녀에게 전달될 다듬어진 문장</span></div>
                <p>{polished}</p>
                {recommendationReason && <small className="recommendation-reason">{recommendationReason}</small>}
                <div className="actions">
                  <button onClick={() => saveAnswer('original')} disabled={loading}>원문으로 남기기</button>
                  <button onClick={() => saveAnswer('polished')} disabled={loading}>추천 문장으로 남기기</button>
                </div>
              </div>
            )}
          </div>
        </div>
        </>
      )}
    </main>
  )
}
