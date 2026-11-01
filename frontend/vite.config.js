import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    port: 8080,
    host: '0.0.0.0',
    proxy: {
      '/analysis': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/users': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  optimizeDeps: {
    include: [
      '@jiaminghi/c-render',
      '@jiaminghi/c-render/lib/plugin/util',
      '@jiaminghi/charts/lib/util/index',
      '@jiaminghi/charts/lib/util',
      '@jiaminghi/charts/lib/extend/index',
      '@jiaminghi/charts',
      '@jiaminghi/color'
    ]
  },
  build: {
    commonjsOptions: {
      include: [/node_modules/]
    }
  }
})
