import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useStore, { API_BASE } from '../store';

const ALPHABET = ['A', 'B', 'C', 'D'];

function ExplainBox({ answerId, token }) {
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [error, setError] = useState('');
  const [shown, setShown] = useState(false);

  const handleExplain = async () => {
    if (shown) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/explain/${answerId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Không thể giải thích.');
      setExplanation(data.explanation || data.explain || JSON.stringify(data));
      setShown(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!shown) {
    return (
      <button
        className="mt-sm bg-primary-container/20 text-on-primary-container border border-primary-container/30 px-sm py-xs rounded-lg font-button text-sm hover:bg-primary-container/30 transition-colors flex items-center gap-xs"
        onClick={handleExplain}
        disabled={loading}
      >
        {loading ? <span className="material-symbols-outlined animate-spin text-[16px]">sync</span> : <span className="material-symbols-outlined text-[16px]">bolt</span>}
        Hỏi AI tại sao tôi sai?
      </button>
    );
  }

  return (
    <div className="mt-sm bg-surface-container rounded-xl p-sm border border-outline-variant/30">
      <div className="flex items-center gap-xs text-secondary font-button text-sm mb-xs">
        <span className="material-symbols-outlined text-[18px]">auto_awesome</span> AI giải thích
      </div>
      {error ? (
        <p className="text-error text-sm">{error}</p>
      ) : (
        <div className="text-on-surface-variant text-sm leading-relaxed">{explanation}</div>
      )}
    </div>
  );
}

export default function QuizPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token, isGuest, getGuestQuizById } = useStore();

  const [questions, setQuestions] = useState([]);
  const [isShared, setIsShared] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState({}); // { questionIndex: selectedOption }
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null); // { score, total, answers: [{answer_id, correct}] }
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isGuest) {
      const mockQuiz = getGuestQuizById(id);
      if (mockQuiz) {
        setQuestions(mockQuiz.questions || []);
        setIsShared(mockQuiz.is_shared || false);
      } else {
        setError('Không tìm thấy quiz demo.');
      }
      setLoading(false);
      return;
    }
    const fetchQuiz = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/quiz/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không tìm thấy Quiz');
        const qs = data.questions || (Array.isArray(data) ? data : []);
        setQuestions(qs);
        setIsShared(data.is_shared || false);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchQuiz();
  }, [id, isGuest, token]);

  const handleToggleShare = async () => {
    if (isGuest) {
      setIsShared(!isShared);
      return;
    }
    setSharing(true);
    try {
      const res = await fetch(`${API_BASE}/api/quiz/${id}/share`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ is_shared: !isShared }),
      });
      if (!res.ok) throw new Error('Lỗi cập nhật chia sẻ');
      setIsShared(!isShared);
    } catch (err) {
      alert(err.message);
    } finally {
      setSharing(false);
    }
  };

  const handleSelect = (option) => {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [current]: option }));
  };

  const handleNext = () => {
    if (current < questions.length - 1) setCurrent((c) => c + 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      if (isGuest) {
        let correct = 0;
        const results = questions.map((q, i) => {
          const selected = answers[i] ?? null;
          const isCorrect = selected === q.correct_answer;
          if (isCorrect) correct++;
          return {
            question_id: q.id,
            selected_answer: selected,
            is_correct: isCorrect,
            correct_answer: q.correct_answer,
          };
        });
        const total = questions.length;
        setResult({
          score: Math.round((correct / total) * 100),
          correct_count: correct,
          total_questions: total,
          results,
        });
        setSubmitted(true);
        setSubmitting(false);
        return;
      }
      const payload = questions.map((q, i) => ({
        question_id: q.id,
        selected_answer: answers[i] ?? null,
      }));
      const res = await fetch(`${API_BASE}/api/quiz/${id}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ answers: payload }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Nộp bài thất bại');
      setResult(data);
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-xl">
        <span className="material-symbols-outlined animate-spin text-secondary text-4xl">sync</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto flex flex-col gap-sm items-center mt-xl">
        <div className="bg-error-container text-on-error-container p-sm rounded-xl mb-md border border-error/20 flex items-center gap-2">
          <span className="material-symbols-outlined">error</span>
          {error}
        </div>
        <button 
          className="bg-surface-container-lowest text-secondary font-button text-button px-md py-sm rounded-full shadow-md border border-outline-variant/20 hover:bg-surface-container-low transition-colors flex items-center"
          onClick={() => navigate('/')}
        >
          <span className="material-symbols-outlined mr-1">arrow_back</span> Về Dashboard
        </button>
      </div>
    );
  }

  if (submitted && result) {
    const correctCount = result.correct_count ?? 0;
    const total = result.total_questions ?? result.total ?? questions.length;
    const pct = Math.round(result.score ?? ((correctCount / total) * 100));

    return (
      <div className="max-w-2xl mx-auto w-full pb-xl">
        {/* Result Header */}
        <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-xl border border-outline-variant/20 flex flex-col items-center mb-xl">
          <div className="w-20 h-20 rounded-full bg-[#fff4e5] text-[#f59e0b] flex items-center justify-center mb-md shadow-[0_0_30px_rgba(245,158,11,0.2)]">
             <span className="material-symbols-outlined text-[40px]">emoji_events</span>
          </div>
          <h2 className="font-h2 text-h2 text-primary mb-sm">Kết quả của bạn</h2>
          <p className="font-body-lg text-body-lg text-on-surface-variant mb-lg text-center">
            {pct >= 80 ? 'Xuất sắc! Bạn đã nắm vững kiến thức!' : pct >= 50 ? 'Tốt! Tiếp tục cố gắng nhé!' : 'Hãy ôn tập thêm nhé!'}
          </p>
          
          <div className="w-32 h-32 rounded-full border-8 border-surface-container flex items-center justify-center relative mb-sm">
            <svg className="absolute inset-0 w-full h-full -rotate-90">
               <circle cx="60" cy="60" r="56" fill="transparent" stroke="currentColor" strokeWidth="8" className="text-secondary opacity-20" />
               <circle cx="60" cy="60" r="56" fill="transparent" stroke="currentColor" strokeWidth="8" className="text-secondary" strokeDasharray="351.8" strokeDashoffset={351.8 - (351.8 * pct) / 100} style={{ transition: 'stroke-dashoffset 1s ease-in-out' }} />
            </svg>
            <span className="font-h2 text-h2 text-primary z-10">{pct}%</span>
          </div>
          <p className="font-body-md text-body-md text-on-surface-variant">
            Đúng <strong className="text-primary text-lg">{correctCount}</strong> / <strong className="text-primary text-lg">{total}</strong> câu
          </p>
        </div>

        {/* Review Section */}
        <h3 className="font-h3 text-h3 text-primary mb-md">Xem lại đáp án</h3>
        <div className="flex flex-col gap-md">
          {questions.map((q, i) => {
            const userAns = answers[i];
            const resultItem = result.answers?.[i] || result.results?.[i];
            const isCorrect = resultItem?.is_correct ?? (userAns === q.correct_answer);
            const correctAns = resultItem?.correct_answer ?? q.correct_answer;
            const answerId = resultItem?.answer_id;

            return (
              <div key={q.id || i} className={`bg-surface-container-lowest rounded-xl p-md border ${isCorrect ? 'border-[#16a34a]/30' : 'border-error/30'} shadow-[0_4px_12px_-4px_rgba(0,35,102,0.05)]`}>
                <div className="flex items-start gap-sm mb-sm">
                  {isCorrect ? (
                    <span className="material-symbols-outlined text-[#16a34a] mt-[2px] shrink-0">check_circle</span>
                  ) : (
                    <span className="material-symbols-outlined text-error mt-[2px] shrink-0">cancel</span>
                  )}
                  <p className="font-body-md text-body-md text-on-background">{i + 1}. {q.question}</p>
                </div>
                
                <div className="pl-[36px] flex flex-col gap-xs">
                  <div className="flex items-center gap-xs text-sm">
                    <span className="text-on-surface-variant">Bạn chọn:</span>
                    <span className={`font-button ${isCorrect ? 'text-[#16a34a]' : 'text-error'}`}>{userAns || 'Không trả lời'}</span>
                  </div>
                  {!isCorrect && (
                    <div className="flex items-center gap-xs text-sm">
                      <span className="text-on-surface-variant">Đáp án đúng:</span>
                      <span className="font-button text-[#16a34a]">{correctAns}</span>
                    </div>
                  )}
                  {!isCorrect && answerId && (
                    <ExplainBox answerId={answerId} token={token} />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-sm mt-xl">
          <button 
            className="flex-1 bg-surface-container-lowest text-secondary font-button text-button py-sm rounded-full shadow-md border border-outline-variant/20 hover:bg-surface-container-low transition-colors flex items-center justify-center gap-xs"
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined text-[18px]">arrow_back</span> Dashboard
          </button>
          <button 
            className="flex-1 bg-secondary text-on-secondary font-button text-button py-sm rounded-full shadow-md hover:-translate-y-0.5 transition-all flex items-center justify-center gap-xs"
            onClick={() => { setSubmitted(false); setCurrent(0); setAnswers({}); setResult(null); }}
          >
            <span className="material-symbols-outlined text-[18px]">refresh</span> Làm lại
          </button>
        </div>
      </div>
    );
  }

  // --- Quiz Screen ---
  const q = questions[current];
  const progress = ((current + 1) / (questions.length || 1)) * 100;
  const optionEntries = q?.options ? Object.entries(q.options) : [];

  return (
    <div className="max-w-2xl mx-auto w-full h-[calc(100vh-12rem)] md:h-auto flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-lg shrink-0">
        <div className="flex items-center gap-sm">
          <button 
            className="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition-colors"
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined">close</span>
          </button>
          <h2 className="font-h3 text-h3 text-primary truncate">Bài Quiz</h2>
        </div>
        
        <div className="flex items-center gap-sm">
          <button 
            className={`px-sm py-[6px] rounded-full font-label-caps text-label-caps flex items-center gap-1 transition-colors ${isShared ? 'bg-[#e6f4ea] text-[#16a34a]' : 'bg-surface-container border border-outline-variant/30 text-on-surface-variant hover:text-secondary'}`}
            onClick={handleToggleShare}
            disabled={sharing}
          >
            {sharing ? <span className="material-symbols-outlined animate-spin text-[14px]">sync</span> : <span className="material-symbols-outlined text-[14px]">{isShared ? 'public' : 'share'}</span>}
            <span className="hidden sm:inline">{isShared ? 'Đã chia sẻ' : 'Chia sẻ'}</span>
          </button>
          <div className="bg-secondary-container/30 text-secondary font-label-caps text-label-caps px-sm py-[6px] rounded-full">
            {current + 1} / {questions.length}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden mb-xl shrink-0">
        <div className="h-full bg-secondary transition-all duration-300" style={{ width: `${progress}%` }}></div>
      </div>

      {error && <div className="bg-error-container text-on-error-container p-sm rounded-xl mb-md border border-error/20 flex items-center gap-2 text-sm shrink-0">
        <span className="material-symbols-outlined">error</span>
        {error}
      </div>}

      {/* Question */}
      <div className="flex-grow flex flex-col overflow-y-auto scrollbar-hide pb-md">
        <h3 className="font-h3 text-h3 text-on-background mb-xl leading-relaxed">
          {q?.question_text || q?.question}
        </h3>

        <div className="flex flex-col gap-sm mt-auto">
          {optionEntries.map(([letter, text]) => {
            const isSelected = answers[current] === letter;
            return (
              <button
                key={letter}
                className={`w-full text-left p-md rounded-xl border transition-all flex items-center gap-md ${isSelected ? 'bg-secondary-container border-secondary shadow-[0_0_15px_rgba(33,112,228,0.15)] text-on-secondary-container scale-[1.01]' : 'bg-surface-container-lowest border-outline-variant/30 hover:border-secondary/50 hover:bg-surface-container-low text-on-background'}`}
                onClick={() => handleSelect(letter)}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-button text-sm shrink-0 transition-colors ${isSelected ? 'bg-secondary text-on-secondary' : 'bg-surface-container text-on-surface-variant'}`}>
                  {letter}
                </div>
                <span className="font-body-md text-body-md">{text}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="flex justify-between items-center mt-md pt-md border-t border-outline-variant/20 shrink-0">
        <button
          className={`flex items-center gap-xs px-md py-sm rounded-full font-button text-button transition-colors ${current === 0 ? 'text-outline-variant cursor-not-allowed' : 'text-on-surface-variant hover:bg-surface-container-low'}`}
          onClick={() => setCurrent((c) => Math.max(0, c - 1))}
          disabled={current === 0}
        >
          <span className="material-symbols-outlined text-[18px]">arrow_back</span> Trước
        </button>

        {current < questions.length - 1 ? (
          <button
            className={`flex items-center gap-xs px-lg py-sm rounded-full font-button text-button transition-all shadow-md ${!answers[current] ? 'bg-surface-container text-outline-variant cursor-not-allowed' : 'bg-secondary text-on-secondary hover:-translate-y-0.5'}`}
            onClick={handleNext}
            disabled={!answers[current]}
          >
            Tiếp <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
          </button>
        ) : (
          <button
            className={`flex items-center gap-xs px-lg py-sm rounded-full font-button text-button transition-all shadow-md ${!answers[current] || submitting ? 'bg-surface-container text-outline-variant cursor-not-allowed' : 'bg-[#16a34a] text-white hover:-translate-y-0.5 shadow-[0_0_20px_rgba(22,163,74,0.3)] animate-pulse'}`}
            onClick={handleSubmit}
            disabled={!answers[current] || submitting}
          >
            {submitting ? (
              <><span className="material-symbols-outlined animate-spin text-[18px]">sync</span> Đang nộp...</>
            ) : (
              <><span className="material-symbols-outlined text-[18px]">emoji_events</span> Nộp bài</>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
