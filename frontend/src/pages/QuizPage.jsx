import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, CheckCircle2, XCircle, ChevronRight, Loader2, Zap, Trophy, Share2, Globe, Brain
} from 'lucide-react';
import useStore, { API_BASE } from '../store';

const ALPHABET = ['A', 'B', 'C', 'D'];
const DIFFICULTY_LABELS = { easy: '😊 Dễ', medium: '🎯 Trung bình', hard: '🔥 Khó' };
const DIFFICULTY_ORDER = { easy: 1, medium: 2, hard: 3 };
const DIFFICULTY_BADGE_CLASS = {
  easy: 'badge-success',
  medium: 'badge-blue',
  hard: 'badge-danger',
};

function getDifficultyInfo(label) {
  if (!label) return null;
  return {
    text: DIFFICULTY_LABELS[label] || label,
    className: DIFFICULTY_BADGE_CLASS[label] || 'badge-purple',
  };
}

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
        className="btn btn-sm"
        onClick={handleExplain}
        disabled={loading}
        style={{
          marginTop: '0.75rem',
          background: 'rgba(139, 92, 246, 0.1)',
          color: 'var(--color-primary-hover)',
          border: '1px solid rgba(139, 92, 246, 0.25)',
        }}
      >
        {loading ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
        Hỏi AI tại sao tôi sai?
      </button>
    );
  }

  return (
    <div className="explain-box">
      <div className="explain-box-header">
        <Zap size={16} /> AI giải thích
      </div>
      {error ? (
        <p style={{ color: 'var(--color-danger)', fontSize: '0.85rem' }}>{error}</p>
      ) : (
        <div className="explain-box-content">{explanation}</div>
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
  const [showDifficulty, setShowDifficulty] = useState(false);
  const [showDifficultyReview, setShowDifficultyReview] = useState(false);

  const resultMap = useMemo(() => {
    const map = new Map();
    const list = result?.answers || result?.results || [];
    list.forEach((r) => {
      if (r?.question_id) map.set(r.question_id, r);
    });
    return map;
  }, [result]);

  useEffect(() => {
    if (isGuest) {
      // Guest mode: dùng mock quiz data
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
        // Guest mode: tính điểm locally
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

  // --- Loading ---
  if (loading) {
    return (
      <div className="empty-state">
        <Loader2 size={32} className="animate-spin" style={{ margin: '0 auto 1rem', display: 'block' }} />
        <p>Đang tải Quiz...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 700, margin: '0 auto' }}>
        <div className="alert alert-error">{error}</div>
        <button className="btn btn-ghost" onClick={() => navigate('/')} style={{ marginTop: '1rem' }}>
          <ArrowLeft size={16} /> Về Dashboard
        </button>
      </div>
    );
  }

  if (submitted && result) {
    const correctCount = result.correct_count ?? 0;
    const total = result.total_questions ?? result.total ?? questions.length;
    const pct = Math.round(result.score ?? ((correctCount / total) * 100));
    const radius = 68;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (pct / 100) * circumference;
    const reviewQuestions = questions.map((q, index) => ({ ...q, _index: index }));

    return (
      <div style={{ maxWidth: 700, margin: '0 auto' }} className="animate-fadeIn">
        <div className="result-card">
          <Trophy size={36} color="var(--color-warning)" style={{ marginBottom: '1rem' }} />
          <h2 style={{ marginBottom: '0.5rem' }}>Kết quả của bạn</h2>
          <p style={{ marginBottom: '2rem' }}>
            {pct >= 80 ? '🎉 Xuất sắc! Bạn đã nắm vững kiến thức!' : pct >= 50 ? '💪 Tốt! Tiếp tục cố gắng nhé!' : '📚 Hãy ôn tập thêm nhé!'}
          </p>

          <div className="result-score-ring">
            <svg width="160" height="160" viewBox="0 0 160 160">
              <circle cx="80" cy="80" r={radius} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
              <circle
                cx="80" cy="80" r={radius} fill="none"
                stroke="url(#scoreGrad)" strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                style={{ transition: 'stroke-dashoffset 1s ease' }}
              />
              <defs>
                <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
            </svg>
            <div className="result-score-text">{pct}%</div>
          </div>

          <p style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>
            Đúng <strong style={{ color: 'var(--text-primary)' }}>{correctCount}</strong> / <strong style={{ color: 'var(--text-primary)' }}>{total}</strong> câu
          </p>
        </div>

        {/* Review Section */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <h3 style={{ margin: 0 }}>Xem lại đáp án</h3>
          <button
            className={`btn btn-sm ${showDifficultyReview ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setShowDifficultyReview((v) => !v)}
            title={showDifficultyReview ? 'Ẩn nhãn độ khó' : 'Hiện nhãn độ khó'}
            style={{ gap: '0.4rem' }}
          >
            <Brain size={14} />
            {showDifficultyReview ? 'Ẩn độ khó' : 'Hiện độ khó'}
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {reviewQuestions.map((q, i) => {
            const originalIndex = q._index ?? i;
            const userAns = answers[originalIndex];
            const resultItem = resultMap.get(q.id) || result.answers?.[originalIndex] || result.results?.[originalIndex];
            const isCorrect = resultItem?.is_correct ?? (userAns === q.correct_answer);
            const correctAns = resultItem?.correct_answer ?? q.correct_answer;
            const answerId = resultItem?.answer_id;
            const diffLabel = q.difficulty_label || q.difficulty?.label;
            const diffInfo = getDifficultyInfo(diffLabel);
            const diffScore = typeof q.difficulty_score === 'number'
              ? Math.round(q.difficulty_score * 100)
              : null;

            return (
              <div key={q.id || i} className="glass-card">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  {isCorrect
                    ? <CheckCircle2 size={20} color="var(--color-success)" style={{ flexShrink: 0, marginTop: 2 }} />
                    : <XCircle size={20} color="var(--color-danger)" style={{ flexShrink: 0, marginTop: 2 }} />
                  }
                  <div style={{ flex: 1 }}>
                    <p style={{ color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.5 }}>
                      {originalIndex + 1}. {q.question_text || q.question}
                    </p>
                    {showDifficultyReview && diffInfo && (
                      <div style={{ marginTop: '0.35rem' }}>
                        <span className={`badge ${diffInfo.className}`} title={diffScore !== null ? `Confidence: ${diffScore}%` : undefined}>
                          {diffInfo.text}{diffScore !== null ? ` (${diffScore}%)` : ''}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                <div style={{ paddingLeft: '1.75rem', fontSize: '0.9rem' }}>
                  <p>
                    <span style={{ color: 'var(--text-muted)' }}>Bạn chọn: </span>
                    <span style={{ color: isCorrect ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: 600 }}>
                      {userAns || 'Không trả lời'}
                    </span>
                  </p>
                  {!isCorrect && (
                    <p style={{ marginTop: '0.25rem' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Đáp án đúng: </span>
                      <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>
                        {correctAns}
                      </span>
                    </p>
                  )}
                  {!isCorrect && answerId && (
                    <ExplainBox answerId={answerId} token={token} />
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
          <button className="btn btn-ghost" onClick={() => navigate('/')}>
            <ArrowLeft size={16} /> Dashboard
          </button>
          <button className="btn btn-primary" onClick={() => { setSubmitted(false); setCurrent(0); setAnswers({}); setResult(null); }}>
            Làm lại
          </button>
        </div>
      </div>
    );
  }

  // --- Quiz Screen ---
  const q = questions[current];
  const progress = ((current + 1) / (questions.length || 1)) * 100;
  // options is { A: "...", B: "...", C: "...", D: "..." } — convert to entries
  const optionEntries = q?.options
    ? Object.entries(q.options)
    : [];
  const diffLabel = q?.difficulty_label || q?.difficulty?.label;
  const diffInfo = getDifficultyInfo(diffLabel);
  const diffScore = typeof q?.difficulty_score === 'number'
    ? Math.round(q.difficulty_score * 100)
    : null;

  return (
    <div className="quiz-page animate-fadeIn">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>
          <ArrowLeft size={16} />
        </button>
        <h2 style={{ flex: 1 }}>Bài Quiz</h2>
        <button
          className={`btn btn-sm ${showDifficulty ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setShowDifficulty((v) => !v)}
          title={showDifficulty ? 'Ẩn nhãn độ khó' : 'Bật nhãn độ khó'}
          style={{ gap: '0.4rem' }}
        >
          <Brain size={14} />
          {showDifficulty ? 'Ẩn độ khó' : 'Độ khó'}
        </button>
        <button 
          className={`btn btn-sm ${isShared ? 'btn-success' : 'btn-ghost'}`}
          onClick={handleToggleShare}
          disabled={sharing}
          title={isShared ? "Hủy công khai" : "Chia sẻ lên Cộng đồng"}
        >
          {sharing ? <Loader2 size={14} className="animate-spin" /> : (isShared ? <Globe size={14} /> : <Share2 size={14} />)}
          {isShared ? 'Đã Công khai' : 'Chia sẻ'}
        </button>
        <span className="badge badge-purple">{current + 1}/{questions.length}</span>
      </div>

      {/* Progress */}
      <div className="quiz-header">
        <div className="quiz-progress-info">
          <span>Tiến độ</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* Question Card */}
      <div className="quiz-question-card">
        <div className="quiz-question-number">Câu hỏi {current + 1}</div>
        <div className="quiz-question-text">{q?.question_text || q?.question}</div>
        {showDifficulty && diffInfo && (
          <div style={{ marginTop: '0.5rem' }}>
            <span className={`badge ${diffInfo.className}`} title={diffScore !== null ? `Confidence: ${diffScore}%` : undefined}>
              {diffInfo.text}{diffScore !== null ? ` (${diffScore}%)` : ''}
            </span>
          </div>
        )}

        <div className="quiz-options">
          {optionEntries.map(([letter, text]) => (
            <button
              key={letter}
              className={`quiz-option${answers[current] === letter ? ' selected' : ''}`}
              onClick={() => handleSelect(letter)}
            >
              <span className="quiz-option-letter">{letter}</span>
              {text}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          className="btn btn-ghost"
          onClick={() => setCurrent((c) => Math.max(0, c - 1))}
          disabled={current === 0}
        >
          <ArrowLeft size={16} /> Trước
        </button>

        {current < questions.length - 1 ? (
          <button
            className="btn btn-primary"
            onClick={handleNext}
            disabled={!answers[current]}
          >
            Tiếp <ChevronRight size={16} />
          </button>
        ) : (
          <button
            className="btn btn-primary btn-lg"
            onClick={handleSubmit}
            disabled={submitting}
            style={{ animation: 'pulse-glow 2s infinite' }}
          >
            {submitting ? (
              <><Loader2 size={16} className="animate-spin" /> Đang nộp...</>
            ) : (
              <><Trophy size={16} /> Nộp bài</>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
