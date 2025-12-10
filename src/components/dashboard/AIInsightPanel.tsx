// src/components/dashboard/AIInsightPanel.tsx
import { useState } from 'react'
import { SparklesIcon } from '@heroicons/react/24/outline'
import type { Category } from '../../types'

interface AIInsightPanelProps {
  category: Category
}

export default function AIInsightPanel({ category }: AIInsightPanelProps) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)

  const exampleQueries: Record<Category, string[]> = {
    phone: [
      '总结一下 iPhone 16 Pro 的发热问题？',
      '小米 15 和三星 S24 谁的口碑更好？',
    ],
    car: [
      '总结一下特斯拉 Model 3 的续航表现？',
      '小米 SU7 和 特斯拉 Model 3 谁的口碑更好？',
    ],
    device: [
      '扫地机器人里，石头 和 科沃斯 哪家差评点更多？',
      '追觅 X40 的避障能力如何？',
    ],
  }

  const handleGenerate = async () => {
    if (!query.trim()) return

    setLoading(true)
    setAnswer(null)

    // 模拟 API 调用
    await new Promise((resolve) => setTimeout(resolve, 1600))

    const mockAnswers: Record<Category, string> = {
      phone: `基于当前样本数据，关于「${query}」的简要分析：

1. **整体评价**：手机在性能和做工上的正向评价占多数，但在散热与续航上存在稳定的抱怨点。
2. **主要正向点**：性能释放、屏幕观感、拍照表现。
3. **主要负向点**：高负载场景下的发热、游戏续航、系统更新后的小 Bug。
4. **竞品对比**：同价位竞品在发热控制上略有优势，但在影像和系统体验上仍有差距。

*提示：当前为链路调试版本，尚未接入真实大模型 API。*`,

      car: `基于当前样本数据，关于「${query}」的简要分析：

1. **整体评价**：该车型在驾驶质感、智能化体验上的正向反馈占比较高。
2. **主要正向点**：加速响应、辅助驾驶体验、座舱静谧性。
3. **主要负向点**：续航与标称略有差距、部分车机系统卡顿或黑屏。
4. **竞品对比**：在智能座舱上具优势，但在补能体验和服务网络上仍有改进空间。

*提示：当前为链路调试版本，尚未接入真实大模型 API。*`,

      device: `基于当前样本数据，关于「${query}」的简要分析：

1. **整体评价**：用户对清洁能力和智能路径规划的认可度较高。
2. **主要正向点**：吸力与拖地能力、自动集尘/自清洁、App 控制体验。
3. **主要负向点**：边角清洁能力、噪音、耗材成本。
4. **竞品对比**：在核心清洁能力上处于第一梯队，但在售后服务和耐用性上评价略有分化。

*提示：当前为链路调试版本，尚未接入真实大模型 API。*`,
    }

    setAnswer(mockAnswers[category])
    setLoading(false)
  }

  const currentExamples = exampleQueries[category] ?? exampleQueries.phone

  return (
    <aside className="rounded-xl border border-slate-200 bg-white px-5 py-5 shadow-sm">
      {/* 标题 + 图标 */}
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-sky-100 shadow">
          <SparklesIcon className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            智能分析助手 AI Insight
          </h3>
          <p className="text-[11px] text-slate-500">
            基于已抓取的评论样本，帮助快速总结品牌口碑、优缺点与竞品对比。
          </p>
        </div>
      </div>

      {/* 示例问题 */}
      <div className="mb-4 space-y-2">
        <p className="text-xs font-medium text-slate-700">试试问我：</p>
        <div className="space-y-2">
          {currentExamples.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setQuery(example)}
              className="block w-full rounded-lg bg-slate-50 px-3 py-2 text-left text-xs text-slate-700 transition hover:bg-sky-50"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* 输入区 */}
      <div className="mb-4">
        <label className="mb-2 block text-xs font-medium text-slate-700">
          输入问题
        </label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="请描述你关心的问题，例如：某个品牌在 B 站最近一周的差评主要集中在哪些方面？"
          rows={4}
          className="w-full resize-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 shadow-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
        />
      </div>

      {/* 按钮 */}
      <button
        type="button"
        onClick={handleGenerate}
        disabled={loading || !query.trim()}
        className="flex w-full items-center justify-center rounded-lg bg-gradient-to-r from-sky-600 to-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-md transition hover:from-sky-700 hover:to-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? (
          <>
            <svg
              className="-ml-1 mr-2 h-4 w-4 animate-spin text-white"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            分析中…
          </>
        ) : (
          <>
            <SparklesIcon className="mr-1.5 h-4 w-4" />
            生成分析
          </>
        )}
      </button>

      {/* 输出区 */}
      {answer ? (
        <div className="mt-5 rounded-lg bg-slate-50 px-3 py-3 text-[11px] text-slate-800">
          <h4 className="mb-1.5 text-xs font-semibold text-slate-900">
            AI 分析结果
          </h4>
          <div className="whitespace-pre-line leading-relaxed">{answer}</div>
        </div>
      ) : (
        <div className="mt-5 rounded-lg bg-slate-50 px-3 py-3 text-[11px] text-slate-500">
          AI 的回答会显示在这里，目前为链路调试版本，尚未接入真实大模型。
        </div>
      )}
    </aside>
  )
}
