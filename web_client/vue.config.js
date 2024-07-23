module.exports = {
  configureWebpack: {
    devServer: {
      disableHostCheck: true,
      host: '127.0.0.1',
      port: '8989',
      https: false,
      hotOnly: false,
      proxy: "http://localhost:8000"
    },
  },
  publicPath: '/'
}
