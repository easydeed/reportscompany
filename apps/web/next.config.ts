import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  reactCompiler: true, // React Compiler ✅
  experimental: { externalDir: true }, // Enable workspace imports
  // Fix Turbopack choosing a wrong workspace root when other lockfiles exist
  // (e.g. a package-lock.json outside this repo).
  turbopack: {
    root: path.resolve(process.cwd(), '../..'),
  },
};

// Wrap with bundle analyzer when ANALYZE=true
const withBundleAnalyzer = process.env.ANALYZE === 'true'
  ? require('@next/bundle-analyzer')({ enabled: true })
  : (config: NextConfig) => config;

export default withBundleAnalyzer(nextConfig);
