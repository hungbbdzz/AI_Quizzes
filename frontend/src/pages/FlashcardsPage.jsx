import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useStore, { API_BASE } from '../store';

export default function FlashcardsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token, isGuest, getGuestFlashcardsByDocId } = useStore();

  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isGuest) {
      const mockCards = getGuestFlashcardsByDocId(id);
      setCards(mockCards);
      setLoading(false);
      return;
    }
    const fetchCards = async () => {
      setLoading(true);
      setError('');
      try {
        const res = await fetch(`${API_BASE}/api/flashcards/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Không tìm thấy Flashcard');
        const list = Array.isArray(data) ? data : data.flashcards || [];
        setCards(list);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchCards();
  }, [id, token, isGuest]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      setFlipped((f) => !f);
    }
    if (e.key === 'ArrowRight') {
      setIndex((i) => {
        const newI = Math.min(i + 1, cards.length - 1);
        if (newI !== i) setFlipped(false);
        return newI;
      });
    }
    if (e.key === 'ArrowLeft') {
      setIndex((i) => {
        const newI = Math.max(i - 1, 0);
        if (newI !== i) setFlipped(false);
        return newI;
      });
    }
  }, [cards.length]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const goNext = () => {
    setIndex((i) => Math.min(i + 1, cards.length - 1));
    setFlipped(false);
  };

  const goPrev = () => {
    setIndex((i) => Math.max(i - 1, 0));
    setFlipped(false);
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

  if (cards.length === 0) {
    return (
      <div className="max-w-2xl mx-auto flex flex-col gap-md items-center mt-xl bg-surface-container-lowest rounded-xl p-xl shadow-ambient border border-outline-variant/20 text-center">
        <span className="material-symbols-outlined text-[48px] text-outline-variant">style</span>
        <h3 className="font-h3 text-h3 text-on-background">Chưa có Flashcard</h3>
        <p className="font-body-md text-body-md text-on-surface-variant">Vui lòng tạo Flashcard từ tài liệu trước.</p>
        <button 
          className="mt-sm bg-secondary text-on-secondary font-button text-button px-md py-sm rounded-full shadow-md hover:-translate-y-0.5 transition-all"
          onClick={() => navigate(`/documents/${id}`)}
        >
          Đến trang Tài liệu
        </button>
      </div>
    );
  }

  const card = cards[index];
  const progress = ((index + 1) / cards.length) * 100;

  return (
    <div className="max-w-2xl mx-auto w-full h-[calc(100vh-12rem)] md:h-auto flex flex-col items-center">
      {/* Header */}
      <div className="flex items-center justify-between mb-lg w-full shrink-0">
        <div className="flex items-center gap-sm">
          <button 
            className="w-10 h-10 rounded-full flex items-center justify-center text-on-surface-variant hover:bg-surface-container-low transition-colors"
            onClick={() => navigate('/')}
          >
            <span className="material-symbols-outlined">close</span>
          </button>
          <h2 className="font-h3 text-h3 text-primary truncate">Thẻ ghi nhớ</h2>
        </div>
        
        <div className="bg-[#e6f4ea] text-[#16a34a] font-label-caps text-label-caps px-sm py-[6px] rounded-full shadow-sm">
          {index + 1} / {cards.length}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-surface-container rounded-full overflow-hidden mb-xl shrink-0">
        <div className="h-full bg-secondary transition-all duration-300" style={{ width: `${progress}%` }}></div>
      </div>

      {/* Flashcard Area */}
      <div 
        className="relative w-full max-w-[400px] aspect-[3/4] perspective-[1000px] cursor-pointer group flex-grow mb-xl"
        onClick={() => setFlipped((f) => !f)}
      >
        <div 
          className="w-full h-full relative transition-transform duration-500 transform-style-3d shadow-hover rounded-2xl"
          style={{ transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
        >
          {/* Front */}
          <div className="absolute inset-0 w-full h-full backface-hidden bg-surface-container-lowest rounded-2xl border border-outline-variant/30 flex flex-col p-xl">
            <span className="font-label-caps text-label-caps text-outline-variant uppercase tracking-widest text-center mb-auto">Khái niệm</span>
            <div className="flex-grow flex items-center justify-center">
              <h3 className="font-h3 text-h3 text-on-background text-center leading-relaxed">
                {card?.front_text || card?.front || 'N/A'}
              </h3>
            </div>
            <p className="font-label-caps text-label-caps text-outline text-center mt-auto animate-pulse">Nhấn để lật</p>
          </div>
          
          {/* Back */}
          <div 
            className="absolute inset-0 w-full h-full backface-hidden bg-secondary rounded-2xl shadow-[0_0_30px_rgba(33,112,228,0.2)] flex flex-col p-xl text-on-secondary"
            style={{ transform: 'rotateY(180deg)' }}
          >
            <span className="font-label-caps text-label-caps text-secondary-fixed-dim uppercase tracking-widest text-center mb-auto">Giải thích</span>
            <div className="flex-grow flex items-center justify-center">
              <p className="font-body-lg text-body-lg text-center leading-relaxed">
                {card?.back_text || card?.back || 'N/A'}
              </p>
            </div>
            <p className="font-label-caps text-label-caps text-secondary-fixed-dim text-center mt-auto">Nhấn để lật lại</p>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="w-full max-w-[400px] flex items-center justify-between shrink-0">
        <button 
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${index === 0 ? 'bg-surface-container text-outline-variant cursor-not-allowed' : 'bg-surface-container-lowest border border-outline-variant/30 shadow-md text-on-surface hover:-translate-x-1 hover:border-secondary'}`}
          onClick={goPrev}
          disabled={index === 0}
        >
          <span className="material-symbols-outlined text-[24px]">arrow_back</span>
        </button>
        
        <button 
          className="flex flex-col items-center gap-1 text-on-surface-variant hover:text-secondary transition-colors"
          onClick={() => setFlipped(f => !f)}
        >
          <span className="material-symbols-outlined text-[28px]">360</span>
          <span className="font-label-caps text-label-caps">Lật (Space)</span>
        </button>
        
        <button 
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all ${index === cards.length - 1 ? 'bg-surface-container text-outline-variant cursor-not-allowed' : 'bg-surface-container-lowest border border-outline-variant/30 shadow-md text-secondary hover:translate-x-1 hover:border-secondary'}`}
          onClick={goNext}
          disabled={index === cards.length - 1}
        >
          <span className="material-symbols-outlined text-[24px]">arrow_forward</span>
        </button>
      </div>

      <style>{`
        .perspective-\\[1000px\\] {
          perspective: 1000px;
        }
        .transform-style-3d {
          transform-style: preserve-3d;
        }
        .backface-hidden {
          backface-visibility: hidden;
          -webkit-backface-visibility: hidden;
        }
      `}</style>
    </div>
  );
}
