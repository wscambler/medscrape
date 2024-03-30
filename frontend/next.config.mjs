/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  output: 'standalone',
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Check if VERBOSE_LOGGING environment variable is set
    if (process.env.VERBOSE_LOGGING === 'true') {
      console.log('Enabling verbose logging');
      config.stats = 'verbose'; // Adjust webpack stats for verbose output
    }

    // Return the altered config
    return config;
  },
};

export default nextConfig;
