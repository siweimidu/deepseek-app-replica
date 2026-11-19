import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from '@rspack/cli'

/**
 * 单独产出 markdown 解析 worker。
 *
 * 不走主配置里的 `new Worker(new URL(...))`：那条路会生成带运行时 chunk 加载的产物，
 * 实测在本项目的构建目标下 worker 脚本根本不执行（连启动探针都收不到）。
 * 这里单独打成**一个自包含的经典脚本**，worker 内部不再有 importScripts / 动态 chunk。
 */

const root = path.dirname(fileURLToPath(import.meta.url))
const targets = ['chrome >= 83', 'edge >= 105', 'safari >= 16', 'firefox >= 110']

export default defineConfig({
  mode: 'production',
  target: 'webworker',
  devtool: false,
  entry: './src/services/markdown/parse.worker.ts',
  output: {
    // 不能 clean：主配置刚把整个 dist 产出来
    clean: false,
    path: path.resolve(root, 'dist/static/js'),
    filename: 'parse-worker.js',
    chunkFormat: 'commonjs',
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    // 将 .js 导入路径解析到同名 .ts、.tsx 或 .js 文件
    extensionAlias: { '.js': ['.ts', '.tsx', '.js'] },
  },
  module: {
    rules: [
      {
        test: /\.(?:[cm]?js|jsx|tsx?)$/,
        exclude: /[\\/]node_modules[\\/]core-js[\\/]/,
        loader: 'builtin:swc-loader',
        options: {
          detectSyntax: 'auto',
          isModule: 'unknown',
          jsc: { externalHelpers: true },
          env: { targets, mode: 'usage', coreJs: '3.51' },
        },
        type: 'javascript/auto',
      },
    ],
  },
  optimization: {
    // 单文件：worker 里不允许再拆 chunk
    splitChunks: false,
    runtimeChunk: false,
    minimize: true,
  },
  performance: { hints: false },
})
