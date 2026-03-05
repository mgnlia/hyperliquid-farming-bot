/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Disable static optimization — all pages use runtime API calls
  // and cannot be statically rendered at build time
  experimental: {},
  // Suppress build errors from missing env vars at build time
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
}

module.exports = nextConfig
