import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useStore, { API_BASE } from '../store';

export default function AuthPage() {
  const [tab, setTab] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const { setAuth, loginAsGuest } = useStore();
  const navigate = useNavigate();

  const handleGuestLogin = () => {
    loginAsGuest();
    navigate('/');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    const endpoint = tab === 'login' ? '/api/auth/login' : '/api/auth/register';

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Đã có lỗi xảy ra.');
      }

      if (tab === 'login') {
        setAuth(data.user, data.access_token);
        navigate('/');
      } else {
        setSuccess('Đăng ký thành công! Hãy kiểm tra email để xác nhận tài khoản.');
        setTab('login');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-container-low flex items-center justify-center p-md text-on-background">
      <div className="bg-surface-container-lowest w-full max-w-md rounded-xl shadow-ambient p-xl border border-outline-variant/20 flex flex-col items-center">
        {/* Logo */}
        <div className="flex flex-col items-center mb-lg">
          <div className="w-14 h-14 rounded-full bg-secondary-container text-on-secondary-container flex items-center justify-center mb-sm">
            <span className="material-symbols-outlined text-[32px]">psychology</span>
          </div>
          <h2 className="font-h2 text-h2 text-primary">QuizMaster</h2>
          <p className="font-body-md text-body-md text-on-surface-variant text-center mt-xs">Học thông minh hơn cùng AI</p>
        </div>

        {/* Tabs */}
        <div className="flex w-full bg-surface-container rounded-lg p-[4px] mb-md border border-outline-variant/10">
          <button
            className={`flex-1 font-button text-button py-xs rounded-md transition-colors ${tab === 'login' ? 'bg-surface-container-lowest text-secondary shadow-[0_2px_4px_rgba(0,0,0,0.05)]' : 'text-on-surface-variant hover:text-on-background'}`}
            onClick={() => { setTab('login'); setError(''); setSuccess(''); }}
          >
            Đăng nhập
          </button>
          <button
            className={`flex-1 font-button text-button py-xs rounded-md transition-colors ${tab === 'register' ? 'bg-surface-container-lowest text-secondary shadow-[0_2px_4px_rgba(0,0,0,0.05)]' : 'text-on-surface-variant hover:text-on-background'}`}
            onClick={() => { setTab('register'); setError(''); setSuccess(''); }}
          >
            Đăng ký
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="w-full bg-error-container text-on-error-container p-sm rounded-lg mb-md border border-error/20 flex items-center gap-xs text-sm">
            <span className="material-symbols-outlined text-[18px]">error</span>
            {error}
          </div>
        )}
        {success && (
          <div className="w-full bg-[#e6f4ea] text-[#16a34a] p-sm rounded-lg mb-md border border-[#16a34a]/20 flex items-center gap-xs text-sm">
            <span className="material-symbols-outlined text-[18px]">check_circle</span>
            {success}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-md">
          <div className="flex flex-col gap-xs">
            <label className="font-label-caps text-label-caps text-on-surface-variant">Email</label>
            <input
              className="w-full bg-surface-container-lowest border border-outline-variant/50 rounded-lg px-sm py-sm font-body-md text-body-md text-on-background focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all outline-none"
              type="email"
              placeholder="ban@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="flex flex-col gap-xs">
            <label className="font-label-caps text-label-caps text-on-surface-variant">Mật khẩu</label>
            <div className="relative w-full">
              <input
                className="w-full bg-surface-container-lowest border border-outline-variant/50 rounded-lg pl-sm pr-[40px] py-sm font-body-md text-body-md text-on-background focus:border-secondary focus:ring-2 focus:ring-secondary/20 transition-all outline-none"
                type={showPass ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                className="absolute right-sm top-1/2 -translate-y-1/2 text-outline-variant hover:text-on-background flex items-center justify-center transition-colors"
                tabIndex="-1"
              >
                <span className="material-symbols-outlined text-[20px]">{showPass ? 'visibility_off' : 'visibility'}</span>
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-secondary text-on-secondary font-button text-button py-sm rounded-full shadow-md hover:-translate-y-0.5 hover:shadow-hover transition-all active:translate-y-0 flex items-center justify-center gap-xs mt-sm"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="material-symbols-outlined animate-spin text-[18px]">sync</span>
                Đang xử lý...
              </>
            ) : tab === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}
          </button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-sm w-full my-lg">
          <div className="flex-1 h-[1px] bg-outline-variant/30"></div>
          <span className="font-label-caps text-label-caps text-outline">Hoặc</span>
          <div className="flex-1 h-[1px] bg-outline-variant/30"></div>
        </div>

        {/* Guest Login */}
        <button
          type="button"
          className="w-full border border-dashed border-outline-variant hover:border-secondary hover:bg-surface-container-low text-on-surface-variant hover:text-secondary font-button text-button py-sm rounded-full transition-colors flex flex-col items-center"
          onClick={handleGuestLogin}
        >
          <span>Dùng thử (Guest Demo)</span>
          <span className="font-label-caps text-label-caps text-outline mt-[2px] font-normal">Không cần đăng ký - Dữ liệu mẫu</span>
        </button>
      </div>
    </div>
  );
}
