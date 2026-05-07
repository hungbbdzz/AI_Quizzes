import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useStore, { API_BASE } from '../store';

const DIFFICULTY_LABELS = { easy: '😊 Dễ', medium: '🎯 Trung bình', hard: '🔥 Khó' };

export default function DocumentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token, fetchDocuments, isGuest, getGuestQuizMap, getGuestFlashcardsByDocId, documents } = useStore();

  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [generatingFlash, setGeneratingFlash] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  // --- Quiz config ---
  const [numQuestions, setNumQuestions] = useState(10);
  const [difficulty, setDifficulty] = useState('medium');

  // --- Flashcard config ---
  const [numFlashcards, setNumFlashcards] = useState(15);

  const [existingQuizzes, setExistingQuizzes] = useState([]);
  const [hasFlashcards, setHasFlashcards] = useState(false);

  useEffect(() => {
    if (isGuest) {
      const found = documents.find((d) => d.id === id);
      setDoc(found || null);
      
      const quizMap = getGuestQuizMap();
      if (quizMap[id]) {
        const q = useStore.getState().getGuestQuizById(quizMap[id]);
        if (q) setExistingQuizzes([q]);
      }
      const fc = getGuestFlashcardsByDocId(id);
      if (fc && fc.length > 0) setHasFlashcards(true);

      setLoading(false);
      return;
    }
    const fetchDocData = async () => {
      try {
        const [docRes, quizRes, flashRes] = await Promise.all([
          fetch(`${API_BASE}/api/documents/${id}`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${API_BASE}/api/quiz`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${API_BASE}/api/flashcards/${id}`, { headers: { Authorization: `Bearer ${token}` } }),
        ]);
        
        if (!docRes.ok) throw new Error('Không tìm thấy tài liệu');
        const docData = await docRes.json();
        setDoc(docData);

        if (quizRes.ok) {
          const quizData = await quizRes.json();
          setExistingQuizzes(quizData.quizzes?.filter(q => q.document_id === id) || []);
        }

        if (flashRes.ok) {
          const flashData = await flashRes.json();
          setHasFlashcards(flashData.flashcards?.length > 0);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchDocData();
  }, [id, token, isGuest, documents]);

  const handleGenerateQuiz = async () => {
    setGeneratingQuiz(true);
    setError('');

    if (isGuest) {
      const quizMap = getGuestQuizMap();
      const quizId = quizMap[id];
      if (quizId) {
        setTimeout(() => navigate(`/quiz/${quizId}`), 800);
      } else {
        setError('Không có quiz demo cho tài liệu này.');
        setGeneratingQuiz(false);
      }
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000);
    try {
      const res = await fetch(`${API_BASE}/api/quiz/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ document_id: id, num_questions: numQuestions, difficulty }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Không thể tạo Quiz');
      navigate(`/quiz/${data.id}`);
    } catch (err) {
      clearTimeout(timeout);
      setError(err.name === 'AbortError'
        ? 'Quá thời gian chờ (2 phút). AI đang bận, vui lòng thử lại.'
        : err.message);
      setGeneratingQuiz(false);
    }
  };

  const handleGenerateFlash = async () => {
    setGeneratingFlash(true);
    setError('');

    if (isGuest) {
      const cards = getGuestFlashcardsByDocId(id);
      if (cards.length > 0) {
        setTimeout(() => navigate(`/flashcards/${id}`), 800);
      } else {
        setError('Không có flashcard demo cho tài liệu này.');
        setGeneratingFlash(false);
      }
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000);
    try {
      const res = await fetch(`${API_BASE}/api/flashcards/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ document_id: id, num_flashcards: numFlashcards }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Không thể tạo Flashcard');
      navigate(`/flashcards/${id}`);
    } catch (err) {
      clearTimeout(timeout);
      setError(err.name === 'AbortError'
        ? 'Quá thời gian chờ (2 phút). AI đang bận, vui lòng thử lại.'
        : err.message);
      setGeneratingFlash(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Bạn có chắc muốn xoá tài liệu này? Hành động không thể hoàn tác.')) return;
    setDeleting(true);
    if (isGuest) {
      setTimeout(() => { navigate('/'); setDeleting(false); }, 500);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/documents/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok && res.status !== 204) throw new Error('Xoá thất bại');
      await fetchDocuments(true);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-xl">
        <span className="material-symbols-outlined animate-spin text-secondary text-4xl">sync</span>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="max-w-2xl mx-auto flex flex-col gap-sm items-center mt-xl">
        {error && <div className="bg-error-container text-on-error-container p-sm rounded-xl mb-md border border-error/20 flex items-center gap-2">
          <span className="material-symbols-outlined">error</span>
          {error}
        </div>}
        <button 
          className="bg-surface-container-lowest text-secondary font-button text-button px-md py-sm rounded-full shadow-md border border-outline-variant/20 hover:bg-surface-container-low transition-colors"
          onClick={() => navigate('/')}
        >
          <span className="material-symbols-outlined align-middle mr-1">arrow_back</span>
          Về Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto w-full">
      {/* Back */}
      <button 
        className="flex items-center text-on-surface-variant hover:text-secondary mb-md font-button text-button transition-colors"
        onClick={() => navigate('/')}
      >
        <span className="material-symbols-outlined mr-1">arrow_back</span>
        Quay lại
      </button>

      {isGuest && (
        <div className="bg-[#e6f4ea] text-[#16a34a] p-sm rounded-xl mb-md border border-[#16a34a]/20 flex items-center gap-2 text-sm">
          <span className="material-symbols-outlined">info</span>
          Chế độ Guest Demo — Dữ liệu mẫu, không được lưu thực sự
        </div>
      )}
      {error && (
        <div className="bg-error-container text-on-error-container p-sm rounded-xl mb-md border border-error/20 flex items-center gap-2 text-sm">
          <span className="material-symbols-outlined">error</span>
          {error}
        </div>
      )}

      {/* Document Info */}
      <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-md mb-md border border-outline-variant/20 flex items-start gap-md">
        <div className="w-14 h-14 rounded-xl bg-secondary-container flex items-center justify-center text-on-secondary-container shrink-0">
          <span className="material-symbols-outlined text-[28px]">description</span>
        </div>
        <div className="flex-grow min-w-0">
          <h2 className="font-h3 text-h3 text-primary truncate mb-1">{doc?.file_name || 'Tài liệu'}</h2>
          <p className="font-body-md text-body-md text-on-surface-variant text-sm mb-2">
            Tải lên: {doc?.created_at ? new Date(doc.created_at).toLocaleDateString('vi-VN') : '—'}
          </p>
          <span className={`inline-flex font-label-caps text-label-caps px-2 py-1 rounded-full ${doc.status === 'ready' ? 'bg-[#e6f4ea] text-[#16a34a]' : 'bg-error-container text-error'}`}>
            {doc.status === 'ready' ? 'Sẵn sàng' : doc.status}
          </span>
        </div>
        <button
          className="w-10 h-10 rounded-full flex items-center justify-center text-error hover:bg-error-container/50 transition-colors shrink-0"
          onClick={handleDelete}
          disabled={deleting}
          title="Xoá tài liệu"
        >
          {deleting ? <span className="material-symbols-outlined animate-spin">sync</span> : <span className="material-symbols-outlined">delete</span>}
        </button>
      </div>

      {doc?.summary_text && (
        <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-md mb-lg border border-outline-variant/20">
          <p className="font-label-caps text-label-caps text-on-surface-variant mb-sm uppercase">Tóm tắt nội dung</p>
          <p className="font-body-md text-body-md text-on-background">{doc.summary_text}</p>
        </div>
      )}

      {/* Action Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
        {/* === QUIZ CARD === */}
        <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-md border border-outline-variant/20 flex flex-col">
          <div className="flex flex-col items-center mb-md">
            <div className="w-14 h-14 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center mb-sm shadow-[0_0_15px_rgba(0,35,102,0.1)]">
              <span className="material-symbols-outlined text-[28px]">quiz</span>
            </div>
            <h3 className="font-h3 text-h3 text-primary">Bộ câu hỏi</h3>
            <p className="font-body-md text-body-md text-on-surface-variant text-sm">AI tạo câu trắc nghiệm</p>
          </div>

          {existingQuizzes.length > 0 && (
            <div className="mb-md">
              <p className="font-label-caps text-label-caps text-on-surface-variant mb-xs">Các quiz đã tạo</p>
              <div className="flex flex-col gap-xs">
                {existingQuizzes.map((q, i) => (
                  <button
                    key={q.id}
                    className="flex items-center gap-xs text-left p-xs rounded-lg hover:bg-surface-container-low transition-colors text-sm font-button text-secondary"
                    onClick={() => navigate(`/quiz/${q.id}`)}
                  >
                    <span className="material-symbols-outlined text-[18px]">history_edu</span>
                    <span className="truncate">{q.title || `Quiz ${i + 1}`} ({q.num_questions} câu)</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Quiz config */}
          <div className="flex gap-sm mt-auto mb-sm">
            <div className="flex-1 flex flex-col gap-1">
              <label className="font-label-caps text-label-caps text-on-surface-variant">Số câu</label>
              <select
                className="bg-surface-container border border-outline-variant/50 rounded-lg p-xs text-sm font-body-md outline-none focus:border-secondary"
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                disabled={generatingQuiz}
              >
                {[5, 10, 15, 20].map(n => <option key={n} value={n}>{n} câu</option>)}
              </select>
            </div>
            <div className="flex-1 flex flex-col gap-1">
              <label className="font-label-caps text-label-caps text-on-surface-variant">Độ khó</label>
              <select
                className="bg-surface-container border border-outline-variant/50 rounded-lg p-xs text-sm font-body-md outline-none focus:border-secondary"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                disabled={generatingQuiz}
              >
                <option value="easy">Dễ</option>
                <option value="medium">TB</option>
                <option value="hard">Khó</option>
              </select>
            </div>
          </div>

          <button
            className="w-full bg-primary text-on-primary font-button text-button py-sm rounded-full shadow-md hover:-translate-y-0.5 transition-all active:translate-y-0 flex items-center justify-center gap-xs"
            onClick={handleGenerateQuiz}
            disabled={generatingQuiz || generatingFlash}
          >
            {generatingQuiz
              ? <><span className="material-symbols-outlined animate-spin text-[18px]">sync</span> {isGuest ? 'Đang mở...' : 'AI đang tạo...'}</>
              : <><span className="material-symbols-outlined text-[18px]">auto_awesome</span> Tạo Quiz Mới</>
            }
          </button>
        </div>

        {/* === FLASHCARD CARD === */}
        <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-md border border-outline-variant/20 flex flex-col">
          <div className="flex flex-col items-center mb-md">
            <div className="w-14 h-14 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center mb-sm shadow-[0_0_15px_rgba(33,112,228,0.1)]">
              <span className="material-symbols-outlined text-[28px]">style</span>
            </div>
            <h3 className="font-h3 text-h3 text-primary">Thẻ ghi nhớ</h3>
            <p className="font-body-md text-body-md text-on-surface-variant text-sm">AI tạo Flashcard</p>
          </div>

          {hasFlashcards && (
            <div className="mb-md">
              <button
                className="w-full bg-secondary-container text-on-secondary-container hover:bg-[#d4e4fc] font-button py-sm rounded-lg transition-colors flex items-center justify-center gap-xs"
                onClick={() => navigate(`/flashcards/${id}`)}
              >
                <span className="material-symbols-outlined text-[18px]">open_in_new</span> Mở Flashcards Đã Tạo
              </button>
            </div>
          )}

          {/* Flashcard config */}
          <div className="mt-auto mb-sm">
            <label className="font-label-caps text-label-caps text-on-surface-variant block mb-1">Số thẻ</label>
            <select
              className="w-full bg-surface-container border border-outline-variant/50 rounded-lg p-xs text-sm font-body-md outline-none focus:border-secondary"
              value={numFlashcards}
              onChange={(e) => setNumFlashcards(Number(e.target.value))}
              disabled={generatingFlash}
            >
              {[10, 15, 20, 30].map(n => <option key={n} value={n}>{n} thẻ</option>)}
            </select>
          </div>

          <button
            className="w-full bg-secondary text-on-secondary font-button text-button py-sm rounded-full shadow-md hover:-translate-y-0.5 transition-all active:translate-y-0 flex items-center justify-center gap-xs"
            onClick={handleGenerateFlash}
            disabled={generatingFlash || generatingQuiz}
          >
            {generatingFlash
              ? <><span className="material-symbols-outlined animate-spin text-[18px]">sync</span> {isGuest ? 'Đang mở...' : 'AI đang tạo...'}</>
              : <><span className="material-symbols-outlined text-[18px]">auto_awesome</span> Tạo Thẻ Mới</>
            }
          </button>
        </div>
      </div>

      {/* AI Loading Overlay */}
      {!isGuest && (generatingQuiz || generatingFlash) && (
        <div className="fixed inset-0 z-[100] bg-background/80 backdrop-blur-md flex flex-col items-center justify-center">
          <div className="w-20 h-20 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center shadow-[0_0_30px_rgba(33,112,228,0.2)] animate-pulse mb-lg">
             <span className="material-symbols-outlined text-[40px] animate-spin">sync</span>
          </div>
          <div className="text-center px-md">
            <h3 className="font-h3 text-h3 text-primary mb-sm">
              {generatingQuiz
                ? `AI đang tạo ${numQuestions} câu quiz ${DIFFICULTY_LABELS[difficulty]}...`
                : `AI đang tạo ${numFlashcards} flashcard...`}
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-sm mx-auto">
              Gemini đang đọc và phân tích tài liệu của bạn.
              <br />Thường mất <strong className="text-secondary">15–40 giây</strong>, vui lòng không tắt trang...
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
