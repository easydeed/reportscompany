import { redirect } from 'next/navigation';

// Redirect to unified branding page
// All user types now use the same branding interface at /app/branding
export default function AffiliateBrandingPage() {
  redirect('/app/branding');
}
