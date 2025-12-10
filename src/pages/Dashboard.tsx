// src/pages/Dashboard.tsx 
import { useState } from 'react'
import TabsRoot from '../components/dashboard/TabsRoot'

export default function Dashboard() {
  const [dataUpdateTime] = useState(new Date().toISOString().split('T')[0])

  return (
    <div className="space-y-5">
      {/* 顶部说明条：轻灰蓝底，写清楚“只是样本 Demo” */}
      <section className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-sky-100 bg-sky-50/70 px-4 py-3 text-xs text-slate-600 shadow-sm">
        <p className="max-w-3xl">
          当前展示为最近一段时间抓取到的 Bilibili / GSM Arena / Reddit 等平台的评论样本数据，
          <span className="font-medium">仅供分析与 Demo 演示</span>，不代表完整舆情面。
        </p>
        <div className="flex items-center gap-1 whitespace-nowrap text-[11px] text-slate-500">
          <span className="text-slate-400">数据更新日期：</span>
          <span className="font-medium text-slate-700">{dataUpdateTime}</span>
        </div>
      </section>

      {/* 主体看板：TabsRoot 内部负责分类切换 / 左右布局 */}
      <TabsRoot />
    </div>
  )
}
