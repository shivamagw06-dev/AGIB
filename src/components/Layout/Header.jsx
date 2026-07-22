// src/components/Header.jsx
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Menu, X, User, LogOut, Sun, Moon, Edit2 } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import SearchButton from "./SearchButton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/lib/supabaseClient';
import { isAdmin } from '@/lib/adminAuth';

const Header = ({ currentPage, setCurrentPage }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [handle, setHandle] = useState('');

  const userIsAdmin = isAdmin(user);

  // load profile handle once user logs in
  useEffect(() => {
    if (!user) {
      setHandle('');
      return;
    }

    let mounted = true;
    supabase
      .from('profiles')
      .select('handle')
      .eq('id', user.id)
      .maybeSingle()
      .then(({ data, error }) => {
        if (!mounted) return;
        if (error) {
          console.error('Profile fetch error:', error);
          setHandle(user.email?.split('@')[0] || 'me');
        } else if (!data) {
          setHandle(user.email?.split('@')[0] || 'me');
        } else {
          setHandle(data.handle || user.email?.split('@')[0] || 'me');
        }
      })
      .catch((err) => {
        console.error('Profile fetch catch:', err);
        if (mounted) setHandle(user.email?.split('@')[0] || 'me');
      });

    return () => {
      mounted = false;
    };
  }, [user]);

  const location = useLocation();

  const navItems = [
    { name: 'Home', path: '/' },
    { name: 'Market Updates', path: '/market-updates' },
    { name: 'Research', path: '/research' },
    { name: 'Company Updates', path: '/company-updates' },
    { name: 'About', path: '/about' },
    { name: 'Contact', path: '/contact' },
  ];

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    if (path === '/market-updates') {
      return location.pathname === '/market-updates' || location.pathname.startsWith('/updates/');
    }
    if (path === '/research') {
      return location.pathname === '/research' || location.pathname.startsWith('/sections/live-articles');
    }
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  const handleNavClick = (path) => {
    navigate(path);
    setMobileMenuOpen(false);
    setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 50);
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
      toast?.({ title: 'Logged out', description: 'You have been signed out.' });
    } catch (err) {
      console.error('Logout failed', err);
      toast?.({ title: 'Logout failed', description: err?.message || 'Try again' });
    } finally {
      setMobileMenuOpen(false);
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-slate-200">
      <nav className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center cursor-pointer"
            onClick={() => handleNavClick('/')}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && handleNavClick('/')}
          >
            <span className="text-xl font-bold text-slate-900 tracking-tight">
              AGI
            </span>
          </motion.div>

          <div className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => (
              <button
                key={item.path}
                type="button"
                onClick={() => handleNavClick(item.path)}
                className={`text-sm font-medium transition-colors whitespace-nowrap px-3 py-2 rounded-md ${
                  isActive(item.path)
                    ? 'text-blue-800 bg-blue-50'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
                aria-current={isActive(item.path) ? 'page' : undefined}
              >
                {item.name}
              </button>
            ))}

            {/* Admin-only Write button */}
            {userIsAdmin && (
              <Button
                variant="secondary"
                onClick={() => {
                  setMobileMenuOpen(false);
                  navigate('/admin');
                }}
                className="inline-flex items-center gap-2 ml-3"
                aria-label="Open CMS"
              >
                <Edit2 className="h-4 w-4" />
                CMS
              </Button>
            )}
          </div>

          {/* Right Side Buttons */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title="Toggle theme"
              aria-pressed={theme === 'dark'}
            >
              {theme === 'dark' ? (
                <Sun className="h-[1.2rem] w-[1.2rem]" aria-hidden />
              ) : (
                <Moon className="h-[1.2rem] w-[1.2rem]" aria-hidden />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>

            {/* Profile / Auth */}
            <div className="hidden lg:block">
              {user ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      <span>{(user.email ?? 'User').split('@')[0]}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate('/profile/edit');
                      }}
                    >
                      Edit Profile
                    </DropdownMenuItem>
                    {handle && (
                      <DropdownMenuItem
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate(`/u/${handle}`);
                        }}
                      >
                        View My Profile
                      </DropdownMenuItem>
                    )}
                    {userIsAdmin && (
                      <DropdownMenuItem
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate('/admin');
                        }}
                      >
                        <Edit2 className="mr-2 h-4 w-4" />
                        Content Studio (CMS)
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout}>
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>Log out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <Button onClick={() => navigate('/login')}>Login / Sign Up</Button>
              )}
            </div>

            {/* Mobile Menu Icon */}
            <div className="lg:hidden">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-menu"
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <motion.div
            id="mobile-menu"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden overflow-hidden"
          >
            <div className="py-4 border-t border-slate-200 flex flex-col items-start bg-white">
              {navItems.map((item) => (
                <button
                  key={item.path}
                  type="button"
                  onClick={() => handleNavClick(item.path)}
                  className={`block w-full text-left px-4 py-3 text-base font-medium ${
                    isActive(item.path)
                      ? 'text-blue-800 bg-blue-50'
                      : 'text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {item.name}
                </button>
              ))}

              <div className="px-4 pt-3 w-full">
                {user ? (
                  <>
                    {userIsAdmin && (
                      <Button
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate('/admin');
                        }}
                        variant="secondary"
                        className="w-full mb-2"
                        aria-label="Open CMS"
                      >
                        ✍️ Content Studio (CMS)
                      </Button>
                    )}

                    <Button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        navigate('/profile/edit');
                      }}
                      variant="outline"
                      className="w-full mb-2"
                    >
                      Edit Profile
                    </Button>

                    {handle && (
                      <Button
                        onClick={() => {
                          setMobileMenuOpen(false);
                          navigate(`/u/${handle}`);
                        }}
                        variant="outline"
                        className="w-full mb-2"
                      >
                        View My Profile
                      </Button>
                    )}

                    <Button
                      onClick={() => {
                        setMobileMenuOpen(false);
                        handleLogout();
                      }}
                      variant="outline"
                      className="w-full"
                    >
                      Log Out
                    </Button>
                  </>
                ) : (
                  <Button
                    onClick={() => {
                      setMobileMenuOpen(false);
                      navigate('/login');
                    }}
                    className="w-full"
                  >
                    Login / Sign Up
                  </Button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </nav>
    </header>
  );
};

export default Header;
