/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable static export for deployment to static hosts
  output: 'export',

  // Base path if deployed to a subdirectory
  // basePath: '/multilingual-deception-bench',

  // Image optimization disabled for static export
  images: {
    unoptimized: true,
  },
}

module.exports = nextConfig
