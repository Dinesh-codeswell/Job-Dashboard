/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.googleusercontent.com',
      },
      {
        protocol: 'https',
        hostname: 'media.licdn.com',
      },
      {
        protocol: 'https',
        hostname: '**.indeed.com',
      },
      {
        protocol: 'https',
        hostname: '**.naukri.com',
      },
    ],
  },
}

module.exports = nextConfig
