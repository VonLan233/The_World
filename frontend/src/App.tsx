import { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useAuthStore } from '@/stores/useAuthStore';
import MainLayout from './components/layout/MainLayout';
import ErrorBoundary from './components/errors/ErrorBoundary';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import CharacterCreatePage from './pages/CharacterCreatePage';
import WorldPage from './pages/WorldPage';
import WorldSetupPage from './pages/WorldSetupPage';
import GalleryPage from './pages/GalleryPage';

function App() {
  const loadUser = useAuthStore((s) => s.loadUser);
  useEffect(() => { loadUser(); }, [loadUser]);

  return (
    <ErrorBoundary>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/character/create" element={<CharacterCreatePage />} />
          <Route path="/world/setup/:worldId" element={<WorldSetupPage />} />
          <Route path="/world/:worldId" element={<WorldPage />} />
          <Route path="/gallery" element={<GalleryPage />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
