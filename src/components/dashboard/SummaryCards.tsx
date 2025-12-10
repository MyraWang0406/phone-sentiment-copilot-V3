// src/components/dashboard/SummaryCards.tsx
import { InformationCircleIcon } from '@heroicons/react/24/outline'
import { useState } from 'react'
import type { DashboardSummary } from '../../types'

interface SummaryCardsProps {
  summary: DashboardSummary
}

interface CardProps {
  title: string
  value: string | number
  tooltip: string
}

function Card({ title, value, tooltip }: CardProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  const displayValue =
    typeof value === 'number' ? value.toLocaleString() : value

  return (
    <div className="relative rounded-xl border border-slate-100 bg-white px-5 py-4 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-100 hover:shadow-md">
      <div className="mb-1.5 flex items-center justify-between">
        <h3 className="text-xs font-medium text-slate-600">{title}</h3>
        <div className="relative">
          <InformationCircleIcon
            className="h-4 w-4 cursor-help text-slate-400"
            onMouseEnter={() => setShowTooltip(true)}
            onMouseLeave={() => setShowTooltip(false)}
          />
          {showTooltip && (
            <div className="absolute right-0 top-5 z-10 w-80 max-w-md rounded-md bg-slate-900 px-3 py-2 text-[11px] text-slate-50 shadow-lg">
              <div className="max-h-56 overflow-y-auto leading-relaxed">
                {tooltip}
              </div>
            </div>
          )}
        </div>
      </div>
      <p className="text-2xl font-semibold tracking-tight text-slate-900">
        {displayValue}
      </p>
    </div>
  )
}

export default function SummaryCards({ summary }: SummaryCardsProps) {
  // 提取品牌名称
  const brandNames = summary.brands.map((b) => b.brand_cn).join('、')

  // 提取所有型号（去重）
  const allModels = new Set<string>()
  summary.brands.forEach((brand) => {
    brand.hot_models.forEach((m) => allModels.add(m))
  })
  const modelNames = Array.from(allModels).join('、')

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <Card
        title="舆情平台数"
        value={summary.platforms.length}
        tooltip={`当前类目下已接入的平台：${summary.platforms.join('、')}`}
      />
      <Card
        title="品牌数量"
        value={summary.brand_count}
        tooltip={`当前类目下覆盖的品牌：${brandNames}`}
      />
      <Card
        title="覆盖型号数"
        value={summary.model_count}
        tooltip={`这些品牌下覆盖的代表型号：${modelNames}`}
      />
      <Card
        title="用户评论数"
        value={summary.user_sentence_count}
        tooltip="当前类目下抓取到的用户评论样本总量（包含 Bilibili / GSM Arena / Reddit 等平台的 Top 评论与典型案例），用于做趋势和结构分析。"
      />
    </div>
  )
}
