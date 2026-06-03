export interface Tender {
  id: number
  filename: string
  file_type: string
  file_size: number
  upload_time: string
  status: '已上传' | '解读中' | '已解读'
}

export interface AnalysisModule {
  id: number
  tender_id: number
  module_index: number
  module_name: string
  content: string | null
  status: '等待中' | '进行中' | '已完成'
}

export interface Bid {
  id: number
  tender_id: number | null
  name: string
  status: string
  create_time: string
}

export interface BidChapter {
  id: number
  bid_id: number
  chapter_index: number
  title: string
  content: string | null
  last_modified: string
}

export interface BidDetail extends Bid {
  chapters: BidChapter[]
}

export interface ComplianceItem {
  id: number
  tender_id: number
  bid_id: number
  item_index: number
  item_desc: string
  category: string
  risk_level: '严重' | '高' | '中' | '低'
  page_ref: string | null
  status: string
  remark: string | null
}

export interface ComplianceSummary {
  severe: number
  high: number
  medium: number
  low: number
}

export interface KnowledgeDoc {
  id: number
  category: string
  title: string
  upload_time: string
}

export interface KnowledgeDocDetail extends KnowledgeDoc {
  content: string | null
}

export interface FileContent {
  filename: string
  full_text: string
  sections: { title: string; content: string; page: number }[]
}

export interface FieldOccurrence {
  chapter_index: number
  chapter_title: string
}

export interface FieldInfo {
  field_name: string
  occurrences: FieldOccurrence[]
}

export interface FieldListResponse {
  bid_id: number
  fields: FieldInfo[]
  total_count: number
}

export interface FillResult {
  ok: boolean
  updated_chapters: number
  filled_fields: string[]
  unfilled_fields: string[]
}

export interface MissingField {
  field_name: string
  description: string
  suggested_chapter_index: number
  suggested_chapter_title: string
  priority: '必须' | '重要' | '建议'
  category: string
}

export interface InspectResult {
  bid_id: number
  missing_fields: MissingField[]
  total_count: number
}
