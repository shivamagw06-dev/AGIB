import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  Plus,
  ExternalLink,
  LogOut,
  ChevronRight,
  Brain,
  Radar,
  Shield,
  LineChart,
  Target,
  Zap,
  Layers,
  Bus,
  Scale,
  BookOpen,
  GraduationCap,
  Activity,
  Briefcase,
  Radio,
  ShieldCheck,
  ClipboardCheck,
  Building2,
  Bell,
  Landmark,
  Gauge,
  GitBranch,
  Compass,
  Network,
  BookMarked,
  FlaskConical,
  Gavel,
  Map,
  BrainCircuit,
  Fingerprint,
  ClipboardList,
  Layers3,
  Package,
  ShieldQuestion,
  FileStack,
  Database,
  Lightbulb,
  ListChecks,
  MessageSquare,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/intelligence-map', label: 'Intelligence Map', icon: Map },
  { to: '/admin/intent-intelligence', label: 'Intent Intelligence', icon: BrainCircuit },
  { to: '/admin/entity-resolution', label: 'Entity Resolution', icon: Fingerprint },
  { to: '/admin/research-planner', label: 'Research Planner', icon: ClipboardList },
  { to: '/admin/context-intelligence', label: 'Context Intelligence', icon: Layers3 },
  { to: '/admin/analyst-router', label: 'Analyst Router', icon: Network },
  { to: '/admin/layer-router', label: 'Layer Router', icon: GitBranch },
  { to: '/admin/acquisition-planner', label: 'Acquisition Planner', icon: Database },
  { to: '/admin/blueprint-engine', label: 'Blueprint Engine', icon: FileStack },
  { to: '/admin/validation-engine', label: 'Validation Engine', icon: ShieldQuestion },
  { to: '/admin/research-execution', label: 'Research Execution', icon: Package },
  { to: '/admin/hypothesis-engine', label: 'Hypothesis Engine', icon: Lightbulb },
  { to: '/admin/research-questions', label: 'Research Questions', icon: ListChecks },
  { to: '/admin/hypothesis-testing', label: 'Hypothesis Testing', icon: FlaskConical },
  { to: '/admin/belief-engine', label: 'Belief Engine', icon: Gauge },
  { to: '/admin/thesis-construction', label: 'Thesis Construction', icon: Landmark },
  { to: '/admin/institutional-debate', label: 'Institutional Debate', icon: MessageSquare },
  { to: '/admin/decision-readiness', label: 'Decision Readiness', icon: ShieldCheck },
  { to: '/admin/reasoning-audit', label: 'Reasoning Audit', icon: ClipboardCheck },
  { to: '/admin/articles/new', label: 'New Article', icon: Plus },
  { to: '/admin/categories', label: 'Categories', icon: FolderOpen },
  { to: '/admin/knowledge', label: 'Knowledge Corpus', icon: Brain },
  { to: '/admin/open-intelligence', label: 'Open Intelligence', icon: Radar },
  { to: '/admin/evidence', label: 'Evidence', icon: Shield },
  { to: '/admin/live-evidence', label: 'Live Evidence (LEO)', icon: Activity },
  { to: '/admin/company-dossiers', label: 'Company Dossiers', icon: Briefcase },
  { to: '/admin/yahoo-provider', label: 'Yahoo Provider', icon: Radio },
  { to: '/admin/data-quality', label: 'Data Quality (DVC)', icon: ShieldCheck },
  { to: '/admin/evidence-completion', label: 'Evidence Completion', icon: ClipboardCheck },
  { to: '/admin/company-analysis', label: 'Company Analysis', icon: Building2 },
  { to: '/admin/institutional-stack', label: 'Institutional Stack', icon: Layers },
  { to: '/admin/accounting-intelligence', label: 'Accounting Intel', icon: Scale },
  { to: '/admin/portfolio-intelligence', label: 'Portfolio Intel', icon: Briefcase },
  { to: '/admin/causal-intelligence', label: 'Causal Intel', icon: GitBranch },
  { to: '/admin/forecast-intelligence', label: 'Forecast Intel', icon: Compass },
  { to: '/admin/knowledge-graph', label: 'Knowledge Graph', icon: Network },
  { to: '/admin/institutional-memory', label: 'Learning & Memory', icon: BookMarked },
  { to: '/admin/simulation-lab', label: 'Simulation Lab', icon: FlaskConical },
  { to: '/admin/decision-engine-v2', label: 'Decision Engine V2', icon: Gavel },
  { to: '/admin/company-monitor', label: 'Company Monitor', icon: Bell },
  { to: '/admin/investment-office', label: 'Investment Office', icon: Landmark },
  { to: '/admin/mission-control', label: 'Mission Control', icon: Gauge },
  { to: '/admin/investment-intelligence', label: 'Investment Intel', icon: LineChart },
  { to: '/admin/forecasting', label: 'Forecasting', icon: Target },
  { to: '/admin/events', label: 'Events', icon: Zap },
  { to: '/admin/context', label: 'Context', icon: Layers },
  { to: '/admin/intelligence-bus', label: 'Intelligence Bus', icon: Bus },
  { to: '/admin/valuation', label: 'Valuation', icon: Scale },
  { to: '/admin/models', label: 'Models', icon: BookOpen },
  { to: '/admin/academy', label: 'Finance Academy', icon: GraduationCap },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="w-64 shrink-0 bg-[#0c1220] text-white flex flex-col border-r border-slate-800">
        <div className="px-5 py-6 border-b border-slate-800">
          <p className="text-[10px] uppercase tracking-[0.2em] text-orange-400 font-semibold">AGIB CMS</p>
          <h1 className="text-lg font-bold mt-1">Content Studio</h1>
          <p className="text-xs text-slate-400 mt-1 truncate">{user?.email}</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}

          <button
            type="button"
            onClick={() => navigate('/admin/articles')}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <FileText size={18} />
            All Articles
          </button>
        </nav>

        <div className="px-3 py-4 border-t border-slate-800 space-y-1">
          <button
            type="button"
            onClick={() => window.open('/', '_blank')}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <ExternalLink size={16} />
            View Website
          </button>
          <button
            type="button"
            onClick={async () => {
              await logout();
              navigate('/login');
            }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 shrink-0 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span>CMS</span>
            <ChevronRight size={14} />
            <span className="text-slate-900 font-medium">Editor</span>
          </div>
          <span className="text-xs text-slate-400">Publish market updates in real time</span>
        </header>

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
