import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@components': path.resolve(__dirname, './src/components'),
        '@pages': path.resolve(__dirname, './src/pages'),
        '@stores': path.resolve(__dirname, './src/stores'),
        '@hooks': path.resolve(__dirname, './src/hooks'),
        '@services': path.resolve(__dirname, './src/services'),
        '@utils': path.resolve(__dirname, './src/utils'),
        '@types': path.resolve(__dirname, './src/types'),
        '@styles': path.resolve(__dirname, './src/styles'),
        '@assets': path.resolve(__dirname, './src/assets'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        // 统一代理到API网关
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
          // 保持路径不变，直接转发到网关
          // 例如: /api/v1/auth -> http://localhost:8000/api/v1/auth
        },
        // WebSocket 协作服务
        '/ws': {
          target: env.VITE_WS_URL || 'ws://localhost:8005',
          ws: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            antd: ['antd', '@ant-design/icons'],
            editor: ['@uiw/react-md-editor'],
            charts: ['echarts', 'echarts-for-react'],
            query: ['@tanstack/react-query'],
            pdf: ['pdf-lib'], // PDF处理相关
          },
        },
      },
    },
    // 定义全局常量
    define: {
      __USE_MOCK__: env.VITE_USE_MOCK === 'true',
    },
  }
})
