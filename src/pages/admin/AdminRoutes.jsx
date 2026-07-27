import { Navigate, Route, Routes } from 'react-router-dom';
import RequireAdmin from '@/components/admin/RequireAdmin';
import AdminLayout from '@/pages/admin/AdminLayout';
import AdminDashboard from '@/pages/admin/Dashboard';
import ArticleEditor from '@/pages/admin/ArticleEditor';
import CategoryManager from '@/pages/admin/CategoryManager';
import KnowledgeFoundation from '@/pages/admin/KnowledgeFoundation';
import OpenIntelligence from '@/pages/admin/OpenIntelligence';
import Evidence from '@/pages/admin/Evidence';
import InvestmentIntelligence from '@/pages/admin/InvestmentIntelligence';
import Forecasting from '@/pages/admin/Forecasting';
import Events from '@/pages/admin/Events';
import ContextAssembly from '@/pages/admin/ContextAssembly';
import IntelligenceBus from '@/pages/admin/IntelligenceBus';
import Valuation from '@/pages/admin/Valuation';
import Models from '@/pages/admin/Models';
import FinanceAcademy from '@/pages/admin/FinanceAcademy';
import LiveEvidence from '@/pages/admin/LiveEvidence';
import CompanyDossiers from '@/pages/admin/CompanyDossiers';
import YahooProvider from '@/pages/admin/YahooProvider';
import DataQuality from '@/pages/admin/DataQuality';
import EvidenceCompletion from '@/pages/admin/EvidenceCompletion';
import CompanyAnalysis from '@/pages/admin/CompanyAnalysis';
import CompanyMonitor from '@/pages/admin/CompanyMonitor';
import InvestmentOfficeAdmin from '@/pages/admin/InvestmentOffice';
import MissionControl from '@/pages/admin/MissionControl';
import InstitutionalStack from '@/pages/admin/InstitutionalStack';
import AccountingIntelligence from '@/pages/admin/AccountingIntelligence';
import PortfolioIntelligence from '@/pages/admin/PortfolioIntelligence';
import CausalIntelligence from '@/pages/admin/CausalIntelligence';
import ForecastIntelligence from '@/pages/admin/ForecastIntelligence';
import KnowledgeGraph from '@/pages/admin/KnowledgeGraph';
import InstitutionalMemory from '@/pages/admin/InstitutionalMemory';
import SimulationLab from '@/pages/admin/SimulationLab';
import DecisionEngineV2 from '@/pages/admin/DecisionEngineV2';
import IntelligenceMap from '@/pages/admin/IntelligenceMap';
import IntentIntelligence from '@/pages/admin/IntentIntelligence';
import EntityResolution from '@/pages/admin/EntityResolution';
import ResearchPlanner from '@/pages/admin/ResearchPlanner';
import AnalystRouter from '@/pages/admin/AnalystRouter';
import ContextIntelligence from '@/pages/admin/ContextIntelligence';
import LayerRouter from '@/pages/admin/LayerRouter';
import AcquisitionPlanner from '@/pages/admin/AcquisitionPlanner';
import BlueprintEngine from '@/pages/admin/BlueprintEngine';
import ValidationEngine from '@/pages/admin/ValidationEngine';
import ResearchExecution from '@/pages/admin/ResearchExecution';
import HypothesisEngine from '@/pages/admin/HypothesisEngine';
import ResearchQuestions from '@/pages/admin/ResearchQuestions';
import HypothesisTesting from '@/pages/admin/HypothesisTesting';
import BeliefEngine from '@/pages/admin/BeliefEngine';
import ThesisConstruction from '@/pages/admin/ThesisConstruction';
import InstitutionalDebate from '@/pages/admin/InstitutionalDebate';
import DecisionReadiness from '@/pages/admin/DecisionReadiness';
import ReasoningAudit from '@/pages/admin/ReasoningAudit';

export default function AdminRoutes() {
  return (
    <RequireAdmin>
      <Routes>
        <Route element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="articles" element={<AdminDashboard />} />
          <Route path="articles/new" element={<ArticleEditor />} />
          <Route path="articles/edit/:slug" element={<ArticleEditor />} />
          <Route path="categories" element={<CategoryManager />} />
          <Route path="knowledge" element={<KnowledgeFoundation />} />
          <Route path="open-intelligence" element={<OpenIntelligence />} />
          <Route path="evidence" element={<Evidence />} />
          <Route path="live-evidence" element={<LiveEvidence />} />
          <Route path="company-dossiers" element={<CompanyDossiers />} />
          <Route path="yahoo-provider" element={<YahooProvider />} />
          <Route path="data-quality" element={<DataQuality />} />
          <Route path="evidence-completion" element={<EvidenceCompletion />} />
          <Route path="company-analysis" element={<CompanyAnalysis />} />
          <Route path="institutional-stack" element={<InstitutionalStack />} />
          <Route path="accounting-intelligence" element={<AccountingIntelligence />} />
          <Route path="portfolio-intelligence" element={<PortfolioIntelligence />} />
          <Route path="causal-intelligence" element={<CausalIntelligence />} />
          <Route path="forecast-intelligence" element={<ForecastIntelligence />} />
          <Route path="knowledge-graph" element={<KnowledgeGraph />} />
          <Route path="institutional-memory" element={<InstitutionalMemory />} />
          <Route path="simulation-lab" element={<SimulationLab />} />
          <Route path="decision-engine-v2" element={<DecisionEngineV2 />} />
          <Route path="company-monitor" element={<CompanyMonitor />} />
          <Route path="investment-office" element={<InvestmentOfficeAdmin />} />
          <Route path="mission-control" element={<MissionControl />} />
          <Route path="intelligence-map" element={<IntelligenceMap />} />
          <Route path="intent-intelligence" element={<IntentIntelligence />} />
          <Route path="entity-resolution" element={<EntityResolution />} />
          <Route path="research-planner" element={<ResearchPlanner />} />
          <Route path="context-intelligence" element={<ContextIntelligence />} />
          <Route path="analyst-router" element={<AnalystRouter />} />
          <Route path="layer-router" element={<LayerRouter />} />
          <Route path="acquisition-planner" element={<AcquisitionPlanner />} />
          <Route path="blueprint-engine" element={<BlueprintEngine />} />
          <Route path="validation-engine" element={<ValidationEngine />} />
          <Route path="research-execution" element={<ResearchExecution />} />
          <Route path="hypothesis-engine" element={<HypothesisEngine />} />
          <Route path="research-questions" element={<ResearchQuestions />} />
          <Route path="hypothesis-testing" element={<HypothesisTesting />} />
          <Route path="belief-engine" element={<BeliefEngine />} />
          <Route path="thesis-construction" element={<ThesisConstruction />} />
          <Route path="institutional-debate" element={<InstitutionalDebate />} />
          <Route path="decision-readiness" element={<DecisionReadiness />} />
          <Route path="reasoning-audit" element={<ReasoningAudit />} />
          <Route path="system" element={<MissionControl />} />
          <Route path="investment-intelligence" element={<InvestmentIntelligence />} />
          <Route path="forecasting" element={<Forecasting />} />
          <Route path="events" element={<Events />} />
          <Route path="context" element={<ContextAssembly />} />
          <Route path="intelligence-bus" element={<IntelligenceBus />} />
          <Route path="valuation" element={<Valuation />} />
          <Route path="models" element={<Models />} />
          <Route path="academy" element={<FinanceAcademy />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Route>
      </Routes>
    </RequireAdmin>
  );
}
