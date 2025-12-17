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

export default nextConfig;
