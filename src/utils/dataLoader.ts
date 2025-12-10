import type { DashboardSummary, UnifiedComment } from '../types'

import phonesSummary from '../data/phones_summary.json'
import carsSummary from '../data/cars_summary.json'
import devicesSummary from '../data/devices_summary.json'
import phonesComments from '../data/phones_comments_sample.json'
import carsComments from '../data/cars_comments_sample.json'
import devicesComments from '../data/devices_comments_sample.json'

export async function loadSummary(category: 'phone' | 'car' | 'device'): Promise<DashboardSummary> {
  // 模拟异步加载
  await new Promise(resolve => setTimeout(resolve, 100))
  
  const data = {
    phone: phonesSummary,
    car: carsSummary,
    device: devicesSummary,
  }
  return data[category] as DashboardSummary
}

export async function loadComments(category: 'phone' | 'car' | 'device'): Promise<UnifiedComment[]> {
  // 模拟异步加载
  await new Promise(resolve => setTimeout(resolve, 100))
  
  const data = {
    phone: phonesComments,
    car: carsComments,
    device: devicesComments,
  }
  return data[category] as UnifiedComment[]
}
