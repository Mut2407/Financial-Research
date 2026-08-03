import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ── Eager (Auth layout is tiny and needed on first paint for unauthenticated users)
import { AuthLayout } from './features/auth/AuthLayout';
import { AppLayout } from './components/layout/AppLayout';

// ── Lazy (Route-level code splitting → each page loaded only when first visited)
const Login = lazy(() => import('./features/auth/Login').then((m) => ({ default: m.Login })));
const Register = lazy(() => import('./features/auth/Register').then((m) => ({ default: m.Register })));
const Dashboard = lazy(() => import('./features/dashboard/Dashboard').then((m) => ({ default: m.Dashboard })));
const CompanyList = lazy(() => import('./features/company/CompanyList').then((m) => ({ default: m.CompanyList })));
const FinancialStatements = lazy(() => import('./features/financial-statements/FinancialStatements').then((m) => ({ default: m.FinancialStatements })));
const DataNormalization = lazy(() => import('./features/data-normalization/DataNormalization').then((m) => ({ default: m.DataNormalization })));
const FinancialRatiosView = lazy(() => import('./features/financial-ratios/FinancialRatiosView').then((m) => ({ default: m.FinancialRatiosView })));
const DistressLabelingView = lazy(() => import('./features/distress-labeling/DistressLabelingView').then((m) => ({ default: m.DistressLabelingView })));
const DatasetExportView = lazy(() => import('./features/dataset-export/DatasetExportView').then((m) => ({ default: m.DatasetExportView })));
const ModelStudioView = lazy(() => import('./features/ai-models/ModelStudioView').then((m) => ({ default: m.ModelStudioView })));
const PredictionDashboardView = lazy(() => import('./features/prediction/PredictionDashboardView').then((m) => ({ default: m.PredictionDashboardView })));
const DataExplorer = lazy(() => import('./features/data-explorer/DataExplorer').then((m) => ({ default: m.DataExplorer })));
const Settings = lazy(() => import('./features/settings/Settings').then((m) => ({ default: m.Settings })));

// ── Suspense Fallback ────────────────────────────────────────────────────────
const PageLoader = () => (
  <div className="flex items-center justify-center h-full min-h-[60vh]">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 rounded-full border-2 border-indigo-200 border-t-indigo-600 animate-spin" />
      <p className="text-sm text-slate-400 font-medium">Loading...</p>
    </div>
  </div>
);

// ── QueryClient (singleton) ──────────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30_000,
    },
  },
});

// ── App ──────────────────────────────────────────────────────────────────────
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public routes */}
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
            </Route>

            {/* Protected routes */}
            <Route element={<AppLayout />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/companies" element={<CompanyList />} />
              <Route path="/financials" element={<FinancialStatements />} />
              <Route path="/normalization" element={<DataNormalization />} />
              <Route path="/ratios" element={<FinancialRatiosView />} />
              <Route path="/distress" element={<DistressLabelingView />} />
              <Route path="/dataset" element={<DatasetExportView />} />
              <Route path="/ai-studio" element={<ModelStudioView />} />
              <Route path="/prediction" element={<PredictionDashboardView />} />
              <Route path="/explorer" element={<DataExplorer />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
