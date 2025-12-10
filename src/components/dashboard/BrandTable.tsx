import { useState } from 'react'
import { ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline'
import type { BrandRow } from '../../types'

interface BrandTableProps {
  brands: BrandRow[]
  onBrandClick: (brandCn: string) => void
}

type SortField = 'total_reviews' | 'positive_rate' | null
type SortDirection = 'asc' | 'desc'

export default function BrandTable({ brands, onBrandClick }: BrandTableProps) {
  const [sortField, setSortField] = useState<SortField>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const handleSort = (field: 'total_reviews' | 'positive_rate') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const sortedBrands = [...brands].sort((a, b) => {
    if (!sortField) return 0
    const aValue = sortField === 'total_reviews' 
      ? a.stats.total_reviews 
      : a.stats.positive_rate
    const bValue = sortField === 'total_reviews'
      ? b.stats.total_reviews
      : b.stats.positive_rate
    
    if (sortDirection === 'asc') {
      return aValue - bValue
    }
    return bValue - aValue
  })

  const SortButton = ({ field, label }: { field: 'total_reviews' | 'positive_rate', label: string }) => (
    <button
      onClick={() => handleSort(field)}
      className="flex items-center space-x-1 hover:text-primary-600"
    >
      <span>{label}</span>
      {sortField === field ? (
        sortDirection === 'asc' ? (
          <ChevronUpIcon className="h-4 w-4" />
        ) : (
          <ChevronDownIcon className="h-4 w-4" />
        )
      ) : (
        <ChevronDownIcon className="h-4 w-4 opacity-30" />
      )}
    </button>
  )

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          品牌舆情概览 共{brands.length}个品牌
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          品牌、代表机型、覆盖平台及情感倾向的汇总视图。
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                品牌
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                热议机型
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                来源
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <SortButton field="total_reviews" label="评论数" />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                正向
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                负向
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                中性
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <SortButton field="positive_rate" label="好评率" />
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedBrands.map((brand, idx) => (
              <tr
                key={idx}
                onClick={() => onBrandClick(brand.brand_cn)}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{brand.brand_cn}</div>
                  <div className="text-sm text-gray-500">{brand.brand_en}</div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1">
                    {brand.hot_models.slice(0, 3).map((model, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {model}
                      </span>
                    ))}
                    {brand.hot_models.length > 3 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-600">
                        +{brand.hot_models.length - 3}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {brand.sources.join(' / ')}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {brand.stats.total_reviews.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">
                  {brand.stats.pos.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                  {brand.stats.neg.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                  {brand.stats.neutral.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {(brand.stats.positive_rate * 100).toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
