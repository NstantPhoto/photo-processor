export interface HotFolderConfig {
  id: string
  path: string
  enabled: boolean
  extensions: string[]
  stabilityTimeout: number // milliseconds to wait for file stability
  priority: 'high' | 'normal' | 'low'
}

export interface FileQueueItem {
  id: string
  path: string
  folderConfigId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  addedAt: Date
  startedAt?: Date
  completedAt?: Date
  fileSize: number
  lastModified: Date
  retryCount: number
  error?: string
}

export interface QueueStatus {
  totalItems: number
  pendingItems: number
  processingItems: number
  completedItems: number
  failedItems: number
  isPaused: boolean
}

export interface WatcherEvent {
  type: 'file_added' | 'file_removed' | 'file_modified' | 'folder_error'
  path: string
  folderId: string
  timestamp: Date
  error?: string
}