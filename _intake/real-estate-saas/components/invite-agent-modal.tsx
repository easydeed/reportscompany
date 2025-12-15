"use client"

import { Button } from '@/components/ui/button';
import { UserPlus } from 'lucide-react';

export function InviteAgentModal() {
  return (
    <Button className="bg-gradient-to-r from-violet-600 to-violet-500 hover:from-violet-700 hover:to-violet-600 text-white shadow-sm">
      <UserPlus className="h-4 w-4 mr-2" />
      Invite Agent
    </Button>
  );
}
