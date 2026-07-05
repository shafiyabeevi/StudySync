import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import StudyPage from './pages/StudyPage';
import ReferencesPage from './pages/ReferencesPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="study/:id" element={<StudyPage />} />
        <Route path="references" element={<ReferencesPage />} />
      </Route>
    </Routes>
  );
}

export default App;
