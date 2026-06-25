import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api/anthropic': {
          target: env.ANTHROPIC_BASE_URL || 'https://api.anthropic.com',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/anthropic/, ''),
          headers: {
            'Authorization': `Bearer ${env.ANTHROPIC_API_KEY}`,
            'anthropic-version': '2023-06-01',
          },
        },
      },
    },
  }
})
