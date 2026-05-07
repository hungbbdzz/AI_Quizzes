import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import useStore from '../store';

export default function Layout() {
  const { user, logout } = useStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  const initials = user?.email ? user.email[0].toUpperCase() : 'U';

  return (
    <div className="min-h-screen bg-background text-on-background flex flex-col">
      {/* Top App Bar (Mobile & Desktop Header) */}
      <header className="fixed top-0 left-0 w-full z-50 bg-surface-container-lowest shadow-md shadow-secondary/5 flex justify-between items-center h-16 px-md md:px-xl">
        <div className="flex items-center gap-md">
          {/* Mobile Profile Avatar */}
          <div className="md:hidden w-10 h-10 rounded-full overflow-hidden bg-surface-container border border-outline-variant/20 flex-shrink-0 cursor-pointer active:scale-95 duration-200 flex items-center justify-center font-bold text-secondary">
            {initials}
          </div>
          <h1 className="font-h3 text-h3 font-bold text-secondary tracking-tight">QuizMaster</h1>
          
          {/* Desktop Nav Links */}
          <div className="hidden md:flex items-center gap-sm ml-lg">
             <NavLink 
                to="/" 
                end
                className={({ isActive }) => 
                  `font-label-caps text-label-caps px-sm py-xs rounded-full transition-colors ${isActive ? 'bg-secondary-container/10 text-secondary' : 'text-on-surface-variant hover:text-secondary'}`
                }
              >
                Home
              </NavLink>
              <NavLink 
                to="/explore" 
                className={({ isActive }) => 
                  `font-label-caps text-label-caps px-sm py-xs rounded-full transition-colors ${isActive ? 'bg-secondary-container/10 text-secondary' : 'text-on-surface-variant hover:text-secondary'}`
                }
              >
                Topics
              </NavLink>
          </div>
        </div>

        <div className="flex items-center gap-md">
          <button aria-label="Notifications" className="w-10 h-10 flex items-center justify-center text-secondary rounded-full hover:bg-secondary-container/10 transition-colors active:scale-95 duration-200">
            <span className="material-symbols-outlined text-[24px]">notifications</span>
          </button>
          {/* Desktop Profile Avatar */}
          <div 
             className="hidden md:flex w-10 h-10 rounded-full bg-surface-container border border-outline-variant/20 cursor-pointer items-center justify-center font-bold text-secondary"
             onClick={handleLogout}
             title="Click to logout"
          >
             {initials}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-grow w-full max-w-[800px] mx-auto px-md md:px-xl pt-24 pb-24 md:pb-8 flex flex-col gap-lg">
        <Outlet />
      </main>

      {/* Bottom Nav Bar (Mobile Only) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 rounded-t-xl bg-surface-container-lowest shadow-[0_-4px_20px_-5px_rgba(0,35,102,0.05)] border-t border-outline-variant/20 flex justify-around items-center h-20 px-sm">
        <NavLink 
          to="/" 
          end
          className={({ isActive }) => 
            `flex flex-col items-center justify-center py-xs px-md rounded-xl transition-all active:scale-90 duration-150 ${isActive ? 'bg-secondary-container text-on-secondary-container' : 'text-on-surface-variant hover:bg-surface-container-low'}`
          }
        >
          {({ isActive }) => (
            <>
              <span className="material-symbols-outlined mb-1" style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}>home</span>
              <span className="font-label-caps text-label-caps">Home</span>
            </>
          )}
        </NavLink>
        
        <NavLink 
          to="/explore" 
          className={({ isActive }) => 
            `flex flex-col items-center justify-center py-xs px-md rounded-xl transition-all active:scale-90 duration-150 ${isActive ? 'bg-secondary-container text-on-secondary-container' : 'text-on-surface-variant hover:bg-surface-container-low'}`
          }
        >
          {({ isActive }) => (
            <>
              <span className="material-symbols-outlined mb-1" style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}>grid_view</span>
              <span className="font-label-caps text-label-caps">Topics</span>
            </>
          )}
        </NavLink>

        <button
          onClick={handleLogout}
          className="flex flex-col items-center justify-center text-on-surface-variant py-xs px-md hover:bg-surface-container-low transition-all active:scale-90 duration-150 rounded-xl"
        >
          <span className="material-symbols-outlined mb-1 text-error">logout</span>
          <span className="font-label-caps text-label-caps">Logout</span>
        </button>
      </nav>
    </div>
  );
}
