import { useRef, useState } from 'react'
import './App.css'
import './QuestionOptions.css'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const emotions = [
  ['지침','◔'], ['불안','≈'], ['기쁨','◡'], ['외로움','○'], ['설렘','✦'], ['슬픔','⌁'],
]
const fallback = '살면서 마음처럼 되지 않았지만, 결국 나를 단단하게 만든 순간은 언제였나요?'
const seeds = [
  { id: 1, emotion:'설렘', date:'8월 28일', author:'엄마', question:'새로운 시작 앞에서 두려웠던 순간이 있었나요?', raw:'그냥 해보는 거지. 하다 보면 길이 보여.', polished:'두려움이 없어서 시작한 건 아니었단다. 완벽한 때를 기다리기보다 오늘 할 수 있는 작은 한 걸음을 내디뎠더니, 길이 조금씩 보이기 시작했어.', thanks:3, moved:2 },
  { id: 2, emotion:'불안', date:'8월 21일', author:'아빠', question:'정답이 없는 선택 앞에서 무엇을 기준으로 결정했나요?', raw:'틀려도 네 선택이면 배울 게 있어.', polished:'완벽한 선택은 없었단다. 내가 중요하게 여기는 것을 먼저 정하고 선택했더니, 결과가 달라도 그 안에서 배울 수 있었어.', thanks:5, moved:3 },
  { id: 3, emotion:'지침', date:'8월 12일', author:'엄마', question:'아무것도 하고 싶지 않을 만큼 지쳤을 때 어떻게 쉬었나요?', raw:'밥 잘 먹고 하루 쉬면 돼.', polished:'앞으로 나아가는 것만이 답은 아니었어. 따뜻한 밥을 먹고 하루를 온전히 쉬는 것도 다시 걷기 위한 중요한 일이었단다.', thanks:4, moved:4 },
]

function Icon({type}) {
  const d = { arrow:'M5 12h14m-5-5 5 5-5 5', back:'m15 18-6-6 6-6', check:'m5 12 4 4L19 6', mic:'M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Zm-6 8a6 6 0 0 0 12 0m-6 6v4m-3 0h6', book:'M4 5.5A2.5 2.5 0 0 1 6.5 3H11v16H6.5A2.5 2.5 0 0 0 4 21.5V5.5Zm16 0A2.5 2.5 0 0 0 17.5 3H13v16h4.5a2.5 2.5 0 0 1 2.5 2.5v-16Z' }[type]
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d={d}/></svg>
}

async function post(path, body) {
  const response = await fetch(API + path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})
  if (!response.ok) throw new Error('request failed')
  return response.json()
}

export default function App() {
  const [screen,setScreen] = useState('child')
  const [emotion,setEmotion] = useState('지침')
  const [worry,setWorry] = useState('')
  const [mode,setMode] = useState('stealth')
  const [question,setQuestion] = useState('')
  const [questionOptions,setQuestionOptions] = useState([])
  const [answer,setAnswer] = useState('')
  const [polished,setPolished] = useState('')
  const [library,setLibrary] = useState(seeds)
  const [loading,setLoading] = useState(false)
  const [notice,setNotice] = useState('')
  const [recording,setRecording] = useState(false)
  const [openRaw,setOpenRaw] = useState(null)
  const timer = useRef()
  const go = (next) => { setScreen(next); setNotice(''); window.scrollTo({top:0,behavior:'smooth'}) }

  async function transform() {
    if (!worry.trim()) return setNotice('마음에 걸리는 일을 한 줄만 들려주세요.')
    setLoading(true); setNotice('')
    try { const r = await post('/api/questions/transform',{worry,emotion,mode}); setQuestionOptions(r.questions||[r.question]); setQuestion(r.question); if(r.source==='local') setNotice('확장된 로컬 질문 엔진으로 3개를 만들었어요.') }
    catch { setQuestionOptions([fallback]); setQuestion(fallback); setNotice('데모 모드로 질문을 만들었어요.') }
    finally { setLoading(false); go('parent') }
  }
  function record() {
    if (recording) { clearTimeout(timer.current); return setRecording(false) }
    setRecording(true); setNotice('아버지의 목소리를 듣고 있어요…')
    timer.current = setTimeout(()=>{ setRecording(false); setAnswer('나도 그때는 막막했지. 그냥 버텼어. 지나고 보니 실패한 시간이 다 쓸모가 있더라.'); setNotice('음성을 글로 옮겼어요.') },2200)
  }
  async function polish() {
    if (!answer.trim()) return setNotice('짧게라도 경험을 들려주세요.')
    setLoading(true)
    try { const r = await post('/api/answers/polish',{answer,question}); setPolished(r.polished) }
    catch { setPolished('나도 그 순간에는 앞이 보이지 않았단다. 그래도 하루씩 견디며 지나고 보니, 그때의 실패가 다음 길을 알아보는 힘이 되어 주었어.') }
    finally { setLoading(false) }
  }
  function save() {
    setLibrary([{id:Date.now(),emotion,date:'오늘',author:'아빠',question,raw:answer,polished,thanks:0,moved:0},...library])
    setAnswer(''); setPolished(''); go('library')
  }
  function react(id,key) { setLibrary(library.map(x=>x.id===id?{...x,[key]:x[key]+1}:x)) }

  return <div className="app">
    <header><button className="brand" onClick={()=>go('child')}><b>슬쩍</b><span>마음을 잇는 작은 질문</span></button><nav><button className={screen==='child'?'on':''} onClick={()=>go('child')}>마음 보내기</button><button className={screen==='parent'?'on':''} onClick={()=>go('parent')}>오늘의 문답</button><button className={screen==='library'?'on':''} onClick={()=>go('library')}>지혜 서재</button></nav><div className="family">우리 가족 <b>김</b></div></header>

    {screen==='child' && <main className="page child">
      <div className="eyebrow">● 오늘의 마음</div><h1>마음에 걸리는 일이 있나요?</h1><p className="lead">직접 말하기 어려운 마음도 괜찮아요.<br/>슬쩍이 자연스러운 질문으로 바꿔 전해드릴게요.</p>
      <section className="paper">
        <Step n="01" title="지금 마음은 어떤가요?" sub="가장 가까운 감정을 하나 골라주세요."/>
        <div className="emotions">{emotions.map(([name,icon])=><button key={name} className={emotion===name?'selected':''} onClick={()=>setEmotion(name)}><i>{icon}</i><span>{name}</span>{emotion===name&&<em><Icon type="check"/></em>}</button>)}</div>
        <hr/><Step n="02" title="무슨 일이 있었나요?" sub="정리되지 않은 말이어도 충분해요."/>
        <label className="field"><textarea value={worry} maxLength="240" onChange={e=>setWorry(e.target.value)} placeholder="예) 면접에서 계속 떨어지는데, 아빠는 실패했을 때 어떻게 버텼어?"/><small>{worry.length} / 240</small></label>
        <hr/><Step n="03" title="어떻게 전할까요?" sub="상황에 맞는 거리를 선택해 주세요."/>
        <div className="modes"><Mode active={mode==='stealth'} onClick={()=>setMode('stealth')} title="슬쩍 모드" tag="완전 익명">내 고민인 줄 모르게, 보편적인 인생 질문으로 전해요.</Mode><Mode active={mode==='hint'} onClick={()=>setMode('hint')} title="살짝 모드" tag="힌트 제공">“자녀가 조언을 기다리고 있어요”라는 힌트를 함께 전해요.</Mode></div>
        {notice&&<p className="notice">{notice}</p>}<Action onClick={transform} loading={loading}>{loading?'질문을 다듬고 있어요':'마음을 질문으로 바꾸기'}</Action><p className="privacy">입력한 고민은 부모님께 그대로 전달되지 않아요.</p>
      </section>
    </main>}

    {screen==='parent' && <main className="page parent">
      <button className="back" onClick={()=>go('child')}><Icon type="back"/> 마음 보내기로</button>
      <div className="hero"><div><div className="eyebrow">● 오늘의 인생 문답</div><h1>아빠의 이야기를 들려주세요.</h1><p className="lead">짧고 투박해도 괜찮아요. 슬쩍이 따뜻한 문장으로 정리해드려요.</p></div><div className="date"><span>SEP</span><b>02</b><small>수요일</small></div></div>
      <section className="question"><div><b>오늘의 질문</b>{mode==='hint'&&<em>자녀가 조언을 기다리고 있어요</em>}</div><blockquote>“{question||fallback}”</blockquote><small>✦ 천천히 떠올려 보세요. 정답은 없어요.</small>{questionOptions.length>1&&<div className="question-options"><p>다른 관점의 질문도 골라보세요</p>{questionOptions.map((item,index)=><button key={item} className={question===item?'selected':''} onClick={()=>setQuestion(item)}><span>{index+1}</span>{item}</button>)}</div>}</section>
      <section className="paper answer"><div className="answer-head"><div><h2>내 경험 들려주기</h2><p>말하거나, 직접 적어도 좋아요.</p></div><span>약 1분</span></div>
        <div className={'recorder '+(recording?'live':'')}><button onClick={record}><Icon type="mic"/></button><div><b>{recording?'듣고 있어요…':'음성으로 편하게 답하기'}</b><small>{recording?'다 말씀하셨으면 버튼을 눌러주세요':'버튼을 누르고 이야기를 시작하세요'}</small></div>{recording&&<div className="wave"><i/><i/><i/><i/><i/></div>}</div>
        <div className="or">또는 직접 적기</div><label className="field"><textarea value={answer} onChange={e=>setAnswer(e.target.value)} placeholder="예) 나도 그때는 막막했지. 그냥 하루하루 버텼어…"/><small>{answer.length}자</small></label>
        <div className="chips"><span>시작이 어렵다면</span>{['처음엔 두려웠지','그래도 버텼어','지나고 보니'].map(x=><button key={x} onClick={()=>setAnswer(answer+(answer?' ':'')+x+'.')}>+ {x}</button>)}</div>
        {notice&&<p className="notice">{notice}</p>}{!polished?<Action onClick={polish} loading={loading}>{loading?'문장을 다듬고 있어요':'✦ 따뜻한 문장으로 다듬기'}</Action>:<div className="polished"><div><b>✦ 슬쩍이 다듬은 문장</b><button onClick={()=>setPolished('')}>다시 쓰기</button></div><p>{polished}</p><div className="actions"><button onClick={()=>setPolished('')}>수정하기</button><button onClick={save}>이대로 전하기 →</button></div></div>}
      </section>
    </main>}

    {screen==='library' && <main className="page library">
      <div className="hero"><div><div className="eyebrow">● 우리 가족 지혜 서재</div><h1>마음 곁에 두고 싶은 이야기</h1><p className="lead">가족이 건넨 삶의 문장들이 한 권의 책처럼 쌓여갑니다.</p></div><div className="count"><Icon type="book"/><b>{library.length}</b><span>개의 이야기</span></div></div>
      <div className="shelf">최근 이야기 <i/></div><div className="wisdom-list">{library.map((x,i)=><article className={'wisdom '+(i===0?'latest':'')} key={x.id}><div className="wisdom-top"><div><span>{x.emotion}의 날</span>{i===0&&<em>NEW</em>}</div><time>{x.date}</time></div><small>{x.question}</small><blockquote>“{x.polished}”</blockquote><div className="author"><b>{x.author[0]}</b><div><strong>{x.author}의 이야기</strong><span>우리 가족에게</span></div></div><div className="wisdom-foot"><div><button onClick={()=>react(x.id,'thanks')}>♡ 고마워요 {x.thanks||''}</button><button onClick={()=>react(x.id,'moved')}>✦ 감동이에요 {x.moved||''}</button></div><button onClick={()=>setOpenRaw(openRaw===x.id?null:x.id)}>{openRaw===x.id?'원문 닫기':'처음 건넨 말 보기'}</button></div>{openRaw===x.id&&<div className="raw"><b>처음 건넨 말</b><p>{x.raw}</p></div>}</article>)}</div><button className="new" onClick={()=>go('child')}>♡ 새로운 마음 보내기</button>
    </main>}
    <footer><b>슬쩍</b><p>말하지 못한 마음과 오래된 지혜 사이</p><small>© 2026 SEUL-JJEOCK · AI Vibethon Team 4</small></footer>
  </div>
}

function Step({n,title,sub}) { return <div className="step"><span>{n}</span><div><h2>{title}</h2><p>{sub}</p></div></div> }
function Mode({active,onClick,title,tag,children}) { return <button className={active?'selected':''} onClick={onClick}><i/><div><b>{title} <em>{tag}</em></b><p>{children}</p></div></button> }
function Action({onClick,loading,children}) { return <button className="action" disabled={loading} onClick={onClick}>{loading&&<i/>}{children}{!loading&&<Icon type="arrow"/>}</button> }
