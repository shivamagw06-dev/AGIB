import { useEffect } from 'react';
import { HedgeFundLabSections } from '@/pages/HedgeFundLab';

export default function HedgeFundPage() {
  useEffect(() => {
    document.title = 'Hedge Fund | Agarwal Global Investments';
  }, []);

  return <HedgeFundLabSections />;
}
