import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { MobileReportViewer } from '@/components/mobile-report/MobileReportViewer';
import { getApiBase } from '@/lib/get-api-base';

interface PageProps {
  params: Promise<{ id: string }>;
}

async function getReportData(id: string) {
  const apiUrl = getApiBase();
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
  
  // No estimate here (D-305, owner decision 2026-10-29). This metadata is the
  // link preview — it shows in texts, Slack and email to anyone the link is
  // forwarded to. The estimate stays in the report, beside how it was worked out.
  const description = 'Home value report: nearby sales, property details and the local market.';
  return {
    title: `Home Value Report | ${report.property.address}`,
    description,
    openGraph: {
      title: `Home Value Report | ${report.property.address}`,
      description,
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

