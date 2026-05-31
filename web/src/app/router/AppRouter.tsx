import { Route, Routes } from 'react-router-dom';

import { HomePage } from '../../features/home/pages/HomePage';
import { BillsPage } from '../../features/bills/pages/BillsPage';
import { BillsApprovedPage } from '../../features/bills/pages/BillsApprovedPage';
import { BillDetailPage } from '../../features/bills/pages/BillDetailPage';
import { PoliticiansSearchPage } from '../../features/politicians/pages/PoliticiansSearchPage';
import { PoliticianHistoryPage } from '../../features/politicians/pages/PoliticianHistoryPage';
import { Shell } from '../shell/Shell';

export function AppRouter() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/leis" element={<BillsPage />} />
        <Route path="/leis-aprovadas" element={<BillsApprovedPage />} />
        <Route path="/leis/:billId" element={<BillDetailPage />} />
        <Route path="/parlamentares" element={<PoliticiansSearchPage />} />
        <Route path="/politicos/:politicianId" element={<PoliticianHistoryPage />} />
      </Route>
    </Routes>
  );
}
