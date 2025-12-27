import { redirect } from 'next/navigation';

type Props = { params: Promise<{ runId: string }> };

/**
 * Social Report Page
 * 
 * This page redirects to the API route handler which serves
 * properly formatted HTML without nested document structure.
 * 
 * The API route (/api/social/[runId]) returns raw HTML with
 * correct content-type headers, which is cleaner for:
 * - Screenshot tools (Playwright, PDFShift)
 * - Browser rendering
 * - SEO and social media crawlers
 */
export default async function SocialReport({ params }: Props) {
  const { runId } = await params;
  
  // Validate UUID format before redirecting
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  
  if (!uuidRegex.test(runId)) {
    return (
      <html lang="en">
        <head>
          <title>Invalid Report ID</title>
          <style>{`
            body {
              width: 1080px;
              height: 1920px;
              margin: 0;
              display: flex;
              align-items: center;
              justify-content: center;
              background: linear-gradient(135deg, #7C3AED 0%, #F26B2B 100%);
              font-family: system-ui, sans-serif;
            }
            .error {
              text-align: center;
              color: white;
              padding: 60px;
            }
            h1 { font-size: 48px; margin-bottom: 20px; }
            p { font-size: 24px; opacity: 0.9; }
          `}</style>
        </head>
        <body>
          <div className="error">
            <h1>Invalid Report ID</h1>
            <p>The provided report ID is not valid.</p>
          </div>
        </body>
      </html>
    );
  }
  
  // Redirect to API route which serves clean HTML
  redirect(`/api/social/${runId}`);
}
