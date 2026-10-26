export function EmailFooter() {
  return (
    <div className="border-t border-[#1B365D]/10 pt-6 mt-2">
      {/* No agent card. This layout receives no agent, and a named person
          with a stock photo and a made-up license number is not a stand-in. */}

      {/* Footer Links */}
      <div className="text-center text-xs text-stone-400">
        {/* Same identity as terms/privacy: the Glendora address and
            support@, and no phone. A sample number here is how a fake
            business line ships the day this layout is imported. */}
        <p className="mb-2">
          TrendyReports &bull; 440 Rte. 66, Glendora, CA 91740
        </p>
        <p className="mb-2">
          <a href="mailto:support@trendyreports.io" className="text-[#1B365D] hover:underline">support@trendyreports.io</a>
        </p>
        <p>
          <a href="#" className="text-[#1B365D] hover:underline">Unsubscribe</a>
          {' '}&bull;{' '}
          <a href="#" className="text-[#1B365D] hover:underline">View Online</a>
          {' '}&bull;{' '}
          <a href="#" className="text-[#1B365D] hover:underline">Privacy Policy</a>
        </p>
      </div>
    </div>
  );
}
