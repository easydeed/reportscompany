import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactCompiler: true, // React Compiler ✅
  experimental: { externalDir: true }, // Enable workspace imports
};

export default nextConfig;
