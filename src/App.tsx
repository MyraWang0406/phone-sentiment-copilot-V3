// src/App.tsx 
import React from 'react'
import Dashboard from './pages/Dashboard'

/**
 * 顶部蓝色 Banner：全局操作栏
 */
const TopBanner: React.FC = () => {
  const today = new Date().toISOString().split('T')[0]

  const handleOpenDocs = () => {
    window.open('https://example.com/usage-docs', '_blank')
  }

  const handleImportData = () => {
    alert('触发「导入数据」弹窗（占位逻辑）')
  }

  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <header className="w-full bg-gradient-to-r from-sky-600 via-sky-600 to-sky-700 text-white shadow-md">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        {/* 左侧：Logo + 标题 + 副标题 */}
        <div className="flex items-start gap-3">
          {/* Logo 图标块 */}
          <div className="mt-1 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/10 shadow-inner backdrop-blur-sm">
            <span className="text-xl">⚡</span>
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg font-semibold leading-tight sm:text-xl">
                锦书舆情 Copilot
              </h1>
              <span className="rounded-full bg-emerald-400/20 px-2 py-0.5 text-[10px] font-bold text-emerald-100 ring-1 ring-inset ring-emerald-400/40">
                Beta
              </span>
            </div>

            {/* 副标题：品类说明 */}
            <p className="mt-1 flex flex-wrap items-center gap-1 text-sm text-sky-50">
              <span className="font-normal opacity-90">
                国内外消费电子品牌舆情洞察 ·
              </span>
              <span className="font-medium">
                智能手机 / 新能源汽车 / 其他大小智能家电
              </span>
            </p>

            <p className="mt-1 text-[10px] text-sky-100/70">
              仅供个人原型展示 · 请勿商用 / 抄袭 / 转载 · 联系作者：
              <span className="underline-offset-2">myrawzm0406@163.com</span> · WeChat: 15301052620
            </p>
          </div>
        </div>

        {/* 右侧：系统状态 + 操作按钮 */}
        <div className="flex flex-col gap-2 sm:items-end">
          {/* 状态行：运行状态 + 更新时间 */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-sky-100/80">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
            </span>
            <span>系统运行中 · BrandSentimentIndex</span>
            <span className="hidden sm:inline">|</span>
            <span>数据更新日期：{today}</span>
          </div>

          {/* 按钮组 */}
          <div className="flex gap-2">
            <button
              onClick={handleOpenDocs}
              className="rounded-lg border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-medium text-white shadow-sm transition hover:bg-white/20"
            >
              使用说明
            </button>
            <button
              onClick={handleImportData}
              className="rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-sky-700 shadow-sm transition hover:bg-slate-50"
            >
              导入数据
            </button>
            <button
              onClick={handleRefresh}
              className="rounded-lg border border-white/15 bg-sky-700/80 px-3 py-1.5 text-xs font-medium text-white shadow-sm transition hover:bg-sky-800"
            >
              刷新
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

/**
 * 右下角水印
 */
const Watermark: React.FC = () => {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-40">
      <div className="pointer-events-auto max-w-xs rounded-lg border border-slate-700 bg-slate-900/95 px-4 py-3 text-[11px] text-slate-200 shadow-xl backdrop-blur">
        <div className="font-semibold text-slate-50">
          锦书舆情 Copilot · 仅供个人原型展示
        </div>
        <div className="mt-1 text-[10px] text-slate-300">
          禁止商用 / 抄袭 / 转载
        </div>
        <div className="mt-2 text-[10px] leading-relaxed text-slate-300">
          联系作者：myrawzm0406@163.com
          <br />
          WeChat: 15301052620
        </div>
      </div>
    </div>
  )
}

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
      <TopBanner />
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-5 sm:px-6 lg:px-8">
        <Dashboard />
      </main>
      <Watermark />
    </div>
  )
}

export default App
