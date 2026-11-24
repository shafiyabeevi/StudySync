import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { BookOpen, GraduationCap, Library, LogOut, Search, Sparkles } from 'lucide-react';
import TeachItBackModal from './TeachItBackModal';
import { useAuth } from '../auth/AuthContext';
import { supabase } from '../lib/supabase';

const Layout = () => {
  const [isTeachModalOpen, setIsTeachModalOpen] = useState(false);
  const [logoutError, setLogoutError] = useState('');
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    setLogoutError('');
    const { error } = await supabase.auth.signOut();
    if (error) {
      console.error('Sign out failed:', error);
      setLogoutError('Could not log out. Please try again.');
      return;
    }
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex shrink-0 items-center gap-2">
              <div className="bg-primary/20 p-2 rounded-lg">
                <BookOpen className="w-6 h-6 text-primary" />
              </div>
              <span className="text-xl font-bold font-mono tracking-tight text-white">Study<span className="text-primary">Sync</span></span>
            </div>
            <div className="flex min-w-0 max-w-[76vw] items-center gap-1 overflow-x-auto sm:max-w-none sm:gap-4">
              <NavLink 
                to="/" 
                className={({isActive}) => 
                  `flex shrink-0 items-center gap-2 whitespace-nowrap px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                <Library className="w-4 h-4" />
                Documents
              </NavLink>
              <NavLink 
                to="/references" 
                className={({isActive}) => 
                  `flex shrink-0 items-center gap-2 whitespace-nowrap px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                <Search className="w-4 h-4" />
                Find Books
              </NavLink>
              <NavLink
                to="/upgrade-me"
                title="Upgrade Me"
                className={({isActive}) =>
                  `flex shrink-0 items-center gap-2 whitespace-nowrap px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                <Sparkles className="w-4 h-4" />
                <span className="hidden lg:inline">Upgrade Me</span>
              </NavLink>
              <button
                type="button"
                onClick={() => setIsTeachModalOpen(true)}
                className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-white/5 hover:text-white"
              >
                <GraduationCap className="w-4 h-4" />
                Teach It Back
              </button>
              <button
                type="button"
                onClick={handleLogout}
                title={user?.email || 'Log out'}
                className="flex shrink-0 items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-white/5 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Log out</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {logoutError && <p role="alert" className="mb-4 text-sm text-red-500">{logoutError}</p>}
        <Outlet />
      </main>
      <TeachItBackModal isOpen={isTeachModalOpen} onClose={() => setIsTeachModalOpen(false)} documentId="" />
    </div>
  );
};

export default Layout;
