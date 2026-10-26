export function EmailFooter() {
  return (
    <div className="border-t border-[#1B365D]/10 pt-6 mt-2">
      <div className="bg-[#1B365D]/5 rounded-xl p-6">
        <div className="flex items-start gap-5">
          {/* Agent Photo */}
          <img
            src="https://randomuser.me/api/portraits/women/44.jpg"
            alt="Sarah Chen"
            className="w-20 h-20 rounded-full object-cover border-2 border-[#1B365D]/20"
          />
          
          {/* Agent Info */}
          <div className="flex-1">
            <p className="font-serif text-lg font-bold text-stone-900 mb-0.5">
              Sarah Chen
            </p>
            <p className="text-xs text-stone-500 mb-3">
              Senior Realtor &bull; DRE #01234567
            </p>
            
            <div className="flex gap-2">
              <a
                href="mailto:support@trendyreports.io"
                className="inline-block px-4 py-1.5 border border-[#1B365D]/20 rounded-md text-[#1B365D] text-xs font-medium hover:bg-[#1B365D]/5 transition"
              >
                support@trendyreports.io
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Links */}
      <div className="text-center mt-6 text-xs text-stone-400">
        {/* Same identity as terms/privacy: the Glendora address and
            support@, and no phone. A sample number here is how a fake
            business line ships the day this layout is imported. */}
        <p className="mb-2">
          TrendyReports &bull; 440 Rte. 66, Glendora, CA 91740
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
