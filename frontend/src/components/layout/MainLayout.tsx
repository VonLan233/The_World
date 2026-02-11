import { Outlet } from 'react-router-dom';
import Header from './Header';

/**
 * Main layout wrapper.
 * Provides the persistent Header and renders page content via <Outlet />.
 */
export default function MainLayout() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
      }}
    >
      <Header />
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Outlet />
      </main>
    </div>
  );
}
