import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { BookOpen, Search, Library, GraduationCap } from 'lucide-react';
import TeachItBackModal from './TeachItBackModal';

const Layout = () => {
  const [isTeachModalOpen, setIsTeachModalOpen] = useState(false);
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="bg-primary/20 p-2 rounded-lg">
                <BookOpen className="w-6 h-6 text-primary" />
              </div>
              <span className="text-xl font-bold font-mono tracking-tight text-white">Study<span className="text-primary">Sync</span></span>
            </div>
            <div className="flex space-x-6">
              <NavLink 
                to="/" 
                className={({isActive}) => 
                  `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
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
                  `flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? 'bg-white/10 text-white' : 'text-gray-300 hover:bg-white/5 hover:text-white'
                  }`
                }
              >
                <Search className="w-4 h-4" />
                Find Books
              </NavLink>
              <button
                type="button"
                onClick={() => setIsTeachModalOpen(true)}
                className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 transition-colors hover:bg-white/5 hover:text-white"
              >
                <GraduationCap className="w-4 h-4" />
                Teach It Back
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>
      <TeachItBackModal isOpen={isTeachModalOpen} onClose={() => setIsTeachModalOpen(false)} documentId="" />
    </div>
  );
};

export default Layout;
