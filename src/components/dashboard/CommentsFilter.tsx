import { useState, useEffect, useMemo } from 'react'
import { Listbox } from '@headlessui/react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'
import type { BrandRow, UnifiedComment, Platform, Sentiment, CommentFilters } from '../../types'

interface CommentsFilterProps {
  brands: BrandRow[]
  comments: UnifiedComment[]
  selectedBrand: string | null
  onFiltersChange?: (filters: CommentFilters) => void
}

export default function CommentsFilter({
  brands,
  comments,
  selectedBrand,
  onFiltersChange,
}: CommentsFilterProps) {
  const [filters, setFilters] = useState<CommentFilters>({
    brands: selectedBrand ? [selectedBrand] : [],
    models: [],
    platforms: [],
    sentiment: 'all',
    year: 'all',
    month: 'all',
  })

  // 从评论中提取可用的选项
  const availableModels = useMemo(() => {
    const modelSet = new Set<string>()
    comments.forEach((c) => {
      if (filters.brands.length === 0 || filters.brands.includes(c.brand_cn)) {
        modelSet.add(c.model_cn)
      }
    })
    return Array.from(modelSet).sort()
  }, [comments, filters.brands])

  const availablePlatforms = useMemo(() => {
    const platformSet = new Set<Platform>()
    comments.forEach((c) => platformSet.add(c.platform))
    return Array.from(platformSet)
  }, [comments])

  const availableYears = useMemo(() => {
    const yearSet = new Set<number>()
    comments.forEach((c) => yearSet.add(c.year))
    return Array.from(yearSet).sort((a, b) => b - a)
  }, [comments])

  useEffect(() => {
    if (selectedBrand) {
      setFilters((prev) => ({
        ...prev,
        brands: [selectedBrand],
      }))
    }
  }, [selectedBrand])

  useEffect(() => {
    onFiltersChange?.(filters)
  }, [filters, onFiltersChange])

  const updateFilter = <K extends keyof CommentFilters>(
    key: K,
    value: CommentFilters[K]
  ) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
  }

  const MultiSelect = ({
    options,
    selected,
    onChange,
  }: {
    options: string[]
    selected: string[]
    onChange: (value: string[]) => void
  }) => (
    <div className="relative">
      <Listbox
        value={selected}
        onChange={onChange}
        multiple
      >
        <Listbox.Button className="relative w-full cursor-default rounded-md bg-white py-2 pl-3 pr-10 text-left text-sm shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500">
          <span className="block truncate">
            {selected.length === 0 ? `选择...` : `已选${selected.length}项`}
          </span>
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
            <ChevronDownIcon className="h-5 w-5 text-gray-400" />
          </span>
        </Listbox.Button>
        <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          {options.map((option) => (
            <Listbox.Option
              key={option}
              value={option}
              className={({ active }) =>
                `relative cursor-default select-none py-2 pl-10 pr-4 ${
                  active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                }`
              }
            >
              {({ selected }) => (
                <>
                  <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                    {option}
                  </span>
                  {selected && (
                    <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-primary-600">
                      ✓
                    </span>
                  )}
                </>
              )}
            </Listbox.Option>
          ))}
        </Listbox.Options>
      </Listbox>
    </div>
  )

  const SingleSelect = <T extends string | number>({
    options,
    selected,
    onChange,
    allLabel = '全部',
  }: {
    options: T[]
    selected: T | 'all'
    onChange: (value: T | 'all') => void
    allLabel?: string
  }) => (
    <div className="relative">
      <Listbox value={selected} onChange={onChange}>
        <Listbox.Button className="relative w-full cursor-default rounded-md bg-white py-2 pl-3 pr-10 text-left text-sm shadow-sm ring-1 ring-inset ring-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-500">
          <span className="block truncate">
            {selected === 'all' ? allLabel : String(selected)}
          </span>
          <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
            <ChevronDownIcon className="h-5 w-5 text-gray-400" />
          </span>
        </Listbox.Button>
        <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
          <Listbox.Option
            value="all"
            className={({ active }) =>
              `relative cursor-default select-none py-2 pl-10 pr-4 ${
                active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
              }`
            }
          >
            {allLabel}
          </Listbox.Option>
          {options.map((option) => (
            <Listbox.Option
              key={option}
              value={option}
              className={({ active }) =>
                `relative cursor-default select-none py-2 pl-10 pr-4 ${
                  active ? 'bg-primary-100 text-primary-900' : 'text-gray-900'
                }`
              }
            >
              {String(option)}
            </Listbox.Option>
          ))}
        </Listbox.Options>
      </Listbox>
    </div>
  )

  return (
    <div className="space-y-4 mb-4">
      <p className="text-sm text-gray-600">
        点击上方品牌行下钻，可按品牌、型号、平台与年月筛选具体评论。
      </p>
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">品牌</label>
          <MultiSelect
            options={brands.map((b) => b.brand_cn)}
            selected={filters.brands}
            onChange={(value) => updateFilter('brands', value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">型号</label>
          <MultiSelect
            options={availableModels}
            selected={filters.models}
            onChange={(value) => updateFilter('models', value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">平台</label>
          <MultiSelect
            options={availablePlatforms}
            selected={filters.platforms}
            onChange={(value) => updateFilter('platforms', value as Platform[])}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">情感</label>
          <SingleSelect<Sentiment | 'all'>
            options={['pos', 'neg', 'neutral']}
            selected={filters.sentiment}
            onChange={(value) => updateFilter('sentiment', value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">年份</label>
          <SingleSelect<number | 'all'>
            options={availableYears}
            selected={filters.year}
            onChange={(value) => updateFilter('year', value)}
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">月份</label>
          <SingleSelect<number | 'all'>
            options={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
            selected={filters.month}
            onChange={(value) => updateFilter('month', value)}
            allLabel="全部月份"
          />
        </div>
      </div>
    </div>
  )
}
