import { Routes, Route } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import CharacterCreatePage from './pages/CharacterCreatePage';
import WorldPage from './pages/WorldPage';
import GalleryPage from './pages/GalleryPage';

function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/character/create" element={<CharacterCreatePage />} />
        <Route path="/world/:worldId" element={<WorldPage />} />
        <Route path="/gallery" element={<GalleryPage />} />
      </Route>
    </Routes>
  );
}

export default App;
