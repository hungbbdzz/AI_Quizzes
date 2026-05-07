import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore, { API_BASE } from '../store';

export default function ExplorePage() {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  
  const { token, isGuest, getGuestQuizMap } = useStore();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCommunityQuizzes = async () => {
      if (isGuest) {
        const mockMap = getGuestQuizMap();
        const mockIds = Object.values(mockMap);
        const mockQuizzes = mockIds.map(id => useStore.getState().getGuestQuizById(id)).filter(Boolean);
        setQuizzes(mockQuizzes);
        setLoading(false);
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/api/quiz/community`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error('Không tải được danh sách');
        const data = await res.json();
        setQuizzes(data.quizzes || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchCommunityQuizzes();
  }, [token, isGuest]);

  const filteredQuizzes = quizzes.filter(q => 
    (q.title || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      {/* Search Section */}
      <section className="mt-lg mb-lg">
        <h2 className="font-h2 text-h2 text-primary mb-md">Explore Topics</h2>
        <div className="relative w-full">
          <span className="material-symbols-outlined absolute left-sm top-1/2 -translate-y-1/2 text-outline">search</span>
          <input 
            className="w-full bg-surface-container-lowest border border-outline-variant/50 rounded-lg py-sm pl-[48px] pr-sm font-body-md text-body-md text-on-surface focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all shadow-ambient outline-none" 
            placeholder="Search for quizzes, topics, or categories..." 
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </section>

      {error && (
        <div className="bg-error-container text-on-error-container p-sm rounded-xl mb-md border border-error/20 flex items-center gap-2">
          <span className="material-symbols-outlined">error</span>
          {error}
        </div>
      )}

      {/* Quizzes Grid */}
      <section>
        <div className="flex justify-between items-center mb-md">
          <h3 className="font-h3 text-h3 text-primary">All Community Quizzes</h3>
        </div>

        {loading ? (
          <div className="flex justify-center p-xl">
            <span className="material-symbols-outlined animate-spin text-secondary text-4xl">sync</span>
          </div>
        ) : filteredQuizzes.length === 0 ? (
          <div className="bg-surface-container-lowest rounded-xl shadow-ambient p-xl border border-outline-variant/20 flex flex-col items-center gap-sm text-center">
            <span className="material-symbols-outlined text-outline-variant text-[48px]">search_off</span>
            <h4 className="font-button text-button text-on-background">Không tìm thấy Quiz</h4>
            <p className="font-body-md text-body-md text-on-surface-variant">Chưa có quiz nào phù hợp hoặc chưa có ai chia sẻ.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
            {filteredQuizzes.map((quiz) => (
              <div 
                key={quiz.id}
                className="bg-surface-container-lowest rounded-xl p-sm flex items-center gap-md border border-outline-variant/20 shadow-[0_5px_15px_-5px_rgba(0,35,102,0.05)] hover:border-secondary hover:bg-surface-container-low transition-all cursor-pointer group"
                onClick={() => navigate(`/quiz/${quiz.id}`)}
              >
                <div className="w-14 h-14 rounded-lg bg-[#eaf1ff] flex items-center justify-center text-secondary shrink-0">
                  <span className="material-symbols-outlined text-[28px]">psychology</span>
                </div>
                <div className="flex-grow min-w-0">
                  <h4 className="font-button text-button text-on-background truncate">{quiz.title}</h4>
                  <p className="font-body-md text-body-md text-on-surface-variant text-sm truncate">
                    Độ khó: {quiz.difficulty || 'TB'}
                  </p>
                </div>
                <div className="px-sm py-xs bg-surface-container rounded-full font-label-caps text-label-caps text-secondary shrink-0">
                  {quiz.num_questions || 0} Qs
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
