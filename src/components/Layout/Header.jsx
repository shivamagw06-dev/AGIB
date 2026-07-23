import { Link } from 'react-router-dom';
import { Search, Menu, X, User, LogOut, Edit2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
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
import Logo from '@/components/Layout/Logo';
import AgiInsightStrip from '@/components/Layout/AgiInsightStrip';
import ResearchSearch from '@/components/Search/ResearchSearch';

const NAV = [
  { name: 'Home', path: '/' },
  { name: 'Market Intelligence', path: '/market-intelligence' },
  { name: 'Pre-Market', path: '/updates/pre-market' },
  { name: '12 PM', path: '/updates/midday' },
  { name: 'Market Close', path: '/updates/market-close' },
  { name: 'Research', path: '/research' },
  { name: 'Company Updates', path: '/company-updates' },
];

export default function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [handle, setHandle] = useState('');
  const userIsAdmin = isAdmin(user);

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
      .then(({ data }) => {
        if (mounted) setHandle(data?.handle || user.email?.split('@')[0] || 'me');
      });
    return () => {
      mounted = false;
    };
  }, [user]);

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  const go = (path) => {
    navigate(path);
    setMobileOpen(false);
    setSearchOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
      toast?.({ title: 'Signed out' });
    } catch (err) {
      toast?.({ title: 'Error', description: err?.message, variant: 'destructive' });
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white shadow-sm">
      <div className="bg-[#001e44] text-white text-[11px]">
        <div className="max-w-[1280px] mx-auto px-4 py-1.5 flex items-center justify-between gap-4">
          <span className="truncate opacity-90">
            Independent equity research · Updated every trading day
          </span>
          <button
            type="button"
            onClick={() => go('/research')}
            className="shrink-0 font-semibold hover:underline hidden sm:inline text-[11px]"
          >
            Explore research →
          </button>
        </div>
      </div>

      <div className="border-b border-[#dddddd]">
        <div className="max-w-[1280px] mx-auto px-4">
          <div className="flex items-center justify-between h-[58px] gap-4">
            <Logo />

            <nav className="hidden lg:flex items-center h-full">
              {NAV.map((item) => (
                <button
                  key={item.path}
                  type="button"
                  onClick={() => go(item.path)}
                  className={`h-full px-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    isActive(item.path)
                      ? 'text-[#111111] border-[#ff6600]'
                      : 'text-[#444444] border-transparent hover:text-[#111111] hover:border-[#cccccc]'
                  }`}
                >
                  {item.name}
                </button>
              ))}
            </nav>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setSearchOpen(true)}
                className="p-2 text-[#111111] hover:bg-[#f5f5f5] rounded-sm"
                aria-label="Search research"
              >
                <Search className="w-5 h-5" />
              </button>

              {user ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="hidden sm:flex h-8 text-xs text-[#111111]">
                      <User className="w-4 h-4 mr-1" />
                      {(user.email ?? '').split('@')[0]}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => go('/profile/edit')}>Edit profile</DropdownMenuItem>
                    {handle && (
                      <DropdownMenuItem onClick={() => go(`/u/${handle}`)}>Public profile</DropdownMenuItem>
                    )}
                    {userIsAdmin && (
                      <DropdownMenuItem onClick={() => go('/admin')}>
                        <Edit2 className="w-4 h-4 mr-2" /> CMS
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout}>
                      <LogOut className="w-4 h-4 mr-2" /> Sign out
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => go('/login')}
                    className="hidden sm:block text-sm font-medium text-[#111111] hover:underline px-2"
                  >
                    Sign in
                  </button>
                  <button
                    type="button"
                    onClick={() => go('/login')}
                    className="hidden sm:block bg-[#111111] text-white text-sm font-bold px-4 py-1.5 hover:bg-[#333]"
                  >
                    Subscribe
                  </button>
                </>
              )}

              {userIsAdmin && (
                <Button
                  variant="outline"
                  size="sm"
                  className="hidden md:flex h-8 text-xs border-[#ddd]"
                  onClick={() => go('/admin')}
                >
                  CMS
                </Button>
              )}

              <button
                type="button"
                className="lg:hidden p-2"
                onClick={() => setMobileOpen(!mobileOpen)}
                aria-label="Menu"
              >
                {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {mobileOpen && (
        <nav className="lg:hidden border-b border-[#ddd] bg-white px-4 py-2">
          {NAV.map((item) => (
            <button
              key={item.path}
              type="button"
              onClick={() => go(item.path)}
              className={`block w-full text-left py-3 text-sm font-medium border-b border-[#eee] ${
                isActive(item.path) ? 'text-[#ff6600]' : 'text-[#111]'
              }`}
            >
              {item.name}
            </button>
          ))}
          {!user && (
            <div className="grid grid-cols-2 gap-2 py-3">
              <button
                type="button"
                onClick={() => go('/login?mode=signin')}
                className="min-h-[44px] border border-[#111111] px-3 text-sm font-bold text-[#111111]"
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => go('/login?mode=signup')}
                className="min-h-[44px] bg-[#111111] px-3 text-sm font-bold text-white"
              >
                Create account
              </button>
            </div>
          )}
        </nav>
      )}

      <AgiInsightStrip />

      {searchOpen && <ResearchSearch onClose={() => setSearchOpen(false)} />}
    </header>
  );
}
