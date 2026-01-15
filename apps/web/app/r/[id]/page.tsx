import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { MobileReportViewer } from '@/components/mobile-report/MobileReportViewer';

interface PageProps {
  params: Promise<{ id: string }>;
}

async function getReportData(id: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const res = await fetch(
    `${apiUrl}/v1/r/${id}/data`,
    { cache: 'no-store' }
  );
  if (!res.ok) return null;
  return res.json();
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const resolvedParams = await params;
  const report = await getReportData(resolvedParams.id);
  if (!report) return { title: 'Report Not Found' };
  
  return {
    title: `Home Value Report | ${report.property.address}`,
    description: `Estimated value: $${report.value_estimate.low.toLocaleString()} - $${report.value_estimate.high.toLocaleString()}`,
    openGraph: {
      title: `Home Value Report | ${report.property.address}`,
      description: `Estimated value: $${report.value_estimate.low.toLocaleString()} - $${report.value_estimate.high.toLocaleString()}`,
    },
  };
}

export default async function MobileReportPage({ params }: PageProps) {
  const resolvedParams = await params;
  const report = await getReportData(resolvedParams.id);
  
  if (!report) {
    notFound();
  }
  
  return <MobileReportViewer report={report} reportId={resolvedParams.id} />;
}

