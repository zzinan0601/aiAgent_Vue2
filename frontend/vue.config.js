const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8888', changeOrigin: true }
    }
  },
  configureWebpack: {
    watchOptions: {
      ignored      : /node_modules|\.git|backend|mcp_server|logs|pagefile/,
      poll         : false,
      aggregateTimeout: 300,
    }
  }
})
