import { useState, useMemo } from 'react'
import type { UnifiedComment, Sentiment } from '../../types'

interface CommentsTableProps {
  comments: UnifiedComment[]
  selectedBrand?: string | null
  filters?: {
    brands?: string[]
    models?: string[]
    platforms?: string[]
    sentiment?: Sentiment | 'all'
    year?: number | 'all'
    month?: number | 'all'
  }
}

const ITEMS_PER_PAGE = 10

export default function CommentsTable({ comments, selectedBrand, filters }: CommentsTableProps) {
  const [currentPage, setCurrentPage] = useState(1)

  const filteredComments = useMemo(() => {
    let result = [...comments]

    // 品牌筛选
    if (selectedBrand) {
      result = result.filter((c) => c.brand_cn === selectedBrand)
    }
    if (filters?.brands && filters.brands.length > 0) {
      result = result.filter((c) => filters.brands!.includes(c.brand_cn))
    }

    // 型号筛选
    if (filters?.models && filters.models.length > 0) {
      result = result.filter((c) => filters.models!.includes(c.model_cn))
    }

    // 平台筛选
    if (filters?.platforms && filters.platforms.length > 0) {
      result = result.filter((c) => filters.platforms!.includes(c.platform))
    }

    // 情感筛选
    if (filters?.sentiment && filters.sentiment !== 'all') {
      result = result.filter((c) => c.sentiment === filters.sentiment)
    }

    // 年份筛选
    if (filters?.year && filters.year !== 'all') {
      result = result.filter((c) => c.year === filters.year)
    }

    // 月份筛选
    if (filters?.month && filters.month !== 'all') {
      result = result.filter((c) => c.month === filters.month)
    }

    // 按时间倒序
    result.sort((a, b) => new Date(b.datetime).getTime() - new Date(a.datetime).getTime())

    return result
  }, [comments, selectedBrand, filters])

  const totalPages = Math.ceil(filteredComments.length / ITEMS_PER_PAGE)
  const paginatedComments = filteredComments.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  )

  const getSentimentBadge = (sentiment: Sentiment) => {
    const config = {
      pos: { label: '正向', className: 'bg-green-100 text-green-800' },
      neg: { label: '负向', className: 'bg-red-100 text-red-800' },
      neutral: { label: '中性', className: 'bg-gray-100 text-gray-800' },
    }
    const { label, className } = config[sentiment]
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${className}`}>
        {label}
      </span>
    )
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (filteredComments.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        {selectedBrand ? '请先在上方表格中选择品牌。' : '暂无评论数据'}
      </div>
    )
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                时间
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                平台
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                品牌
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                型号
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                情感
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                点赞数
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                评论内容
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedComments.map((comment) => (
              <tr key={comment.id} className="hover:bg-gray-50">
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(comment.datetime)}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                  {comment.platform}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                  {comment.brand_cn}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                  {comment.model_cn}
                </td>
                <td className="px-4 py-4 whitespace-nowrap">
                  {getSentimentBadge(comment.sentiment)}
                </td>
                <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500">
                  {comment.like_count?.toLocaleString() || '-'}
                </td>
                <td className="px-4 py-4 text-sm text-gray-900 max-w-md">
                  <div className="truncate" title={comment.content}>
                    {comment.title && (
                      <div className="font-medium text-gray-700 mb-1">{comment.title}</div>
                    )}
                    <div>{comment.content}</div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 mt-4">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              上一页
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              下一页
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                显示 <span className="font-medium">{(currentPage - 1) * ITEMS_PER_PAGE + 1}</span> 到{' '}
                <span className="font-medium">
                  {Math.min(currentPage * ITEMS_PER_PAGE, filteredComments.length)}
                </span>{' '}
                条，共 <span className="font-medium">{filteredComments.length}</span> 条
              </p>
            </div>
            <div>
              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  上一页
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((page) => {
                    // 只显示当前页附近的页码
                    return (
                      page === 1 ||
                      page === totalPages ||
                      (page >= currentPage - 1 && page <= currentPage + 1)
                    )
                  })
                  .map((page, idx, arr) => (
                    <div key={page}>
                      {idx > 0 && arr[idx - 1] !== page - 1 && (
                        <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300">
                          ...
                        </span>
                      )}
                      <button
                        onClick={() => setCurrentPage(page)}
                        className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                          currentPage === page
                            ? 'z-10 bg-primary-600 text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600'
                            : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                        }`}
                      >
                        {page}
                      </button>
                    </div>
                  ))}
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  下一页
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
