import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
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
    port: 3000,
    proxy: {
      // 用户服务（开发时直接连接用户服务端口）
      '/api/v1/auth': {
        target: 'http://localhost:9001',
        changeOrigin: true,
      },
      '/api/v1/users': {
        target: 'http://localhost:9001',
        changeOrigin: true,
      },
      '/api/v1/teams': {
        target: 'http://localhost:9001',
        changeOrigin: true,
      },
      // WebSocket 协作服务
      '/ws': {
        target: 'ws://localhost:8006',
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
        },
      },
    },
  },
})
