// src/components/dashboard/TabsRoot.tsx
import { Tab } from '@headlessui/react'
import { useState, useEffect } from 'react'
import type {
  DashboardSummary,
  UnifiedComment,
  Category,
  CommentFilters,
} from '../../types'
import { loadSummary, loadComments } from '../../utils/dataLoader'
import SummaryCards from './SummaryCards'
import BrandTable from './BrandTable'
import CommentsFilter from './CommentsFilter'
import CommentsTable from './CommentsTable'
import AIInsightPanel from './AIInsightPanel'

interface TabsRootProps {
  onCategoryChange?: (category: Category) => void
}

export default function TabsRoot({ onCategoryChange }: TabsRootProps) {
  const [activeCategory, setActiveCategory] = useState<Category>('phone')
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [comments, setComments] = useState<UnifiedComment[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null)
  const [filters, setFilters] = useState<CommentFilters | null>(null)

  const categories = [
    { key: 'phone' as Category, label: '智能手机' },
    { key: 'car' as Category, label: '新能源汽车' },
    { key: 'device' as Category, label: '其他智能家电' },
  ]

  const selectedIndex = categories.findIndex((c) => c.key === activeCategory)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const [summaryData, commentsData] = await Promise.all([
          loadSummary(activeCategory),
          loadComments(activeCategory),
        ])
        setSummary(summaryData)
        setComments(commentsData)
        onCategoryChange?.(activeCategory)
        setSelectedBrand(null)
        setFilters(null)
      } catch (error) {
        console.error('Failed to load data:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [activeCategory, onCategoryChange])

  const handleBrandClick = (brandCn: string) => {
    setSelectedBrand(brandCn)
  }

  if (loading || !summary) {
    return (
      <div className="flex min-h-[320px] items-center justify-center rounded-xl border border-slate-100 bg-white shadow-sm">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <svg
            className="h-5 w-5 animate-spin text-sky-500"
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
          <span>数据加载中，请稍候…</span>
        </div>
      </div>
    )
  }

  return (
    <Tab.Group
      selectedIndex={selectedIndex}
      onChange={(index) => {
        const next = categories[index]
        if (next) setActiveCategory(next.key)
      }}
    >
      {/* 分类 Tab 切换条 */}
      <div className="mb-4 border-b border-slate-200">
        <Tab.List className="-mb-px flex space-x-8">
          {categories.map((cat) => (
            <Tab
              key={cat.key}
              className={({ selected }) =>
                [
                  'relative whitespace-nowrap border-b-2 py-3 text-sm font-medium outline-none transition-colors',
                  selected
                    ? 'border-sky-600 text-sky-700'
                    : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700',
                ].join(' ')
              }
            >
              {cat.label}
            </Tab>
          ))}
        </Tab.List>
      </div>

      {/* Panels */}
      <Tab.Panels>
        {categories.map((cat) => (
          <Tab.Panel
            key={cat.key}
            className="focus:outline-none"
          >
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3 transition-opacity duration-200">
              {/* 左侧：指标卡 + 品牌表 + 评论透视 */}
              <div className="space-y-6 lg:col-span-2">
                <SummaryCards summary={summary} />

                <BrandTable
                  brands={summary.brands}
                  onBrandClick={handleBrandClick}
                />

                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <h3 className="mb-4 text-base font-semibold text-slate-800">
                    评论透视 & 详细归因
                  </h3>
                      <CommentsFilter
                        brands={summary.brands}
                        comments={comments}
                        selectedBrand={selectedBrand}
                        onFiltersChange={setFilters}
                      />
                  <div className="mt-4">
                    <CommentsTable
                      comments={comments}
                      selectedBrand={selectedBrand}
                      filters={filters || undefined}
                    />
                  </div>
                </div>
              </div>

              {/* 右侧：AI Insight 固定在视窗内 */}
              <div className="lg:col-span-1">
                <div className="sticky top-24">
                  <AIInsightPanel category={activeCategory} />
                </div>
              </div>
            </div>
          </Tab.Panel>
        ))}
      </Tab.Panels>
    </Tab.Group>
  )
}
