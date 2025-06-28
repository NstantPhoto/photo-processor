export interface ImageInfo {
  id: string
  path: string
  width: number
  height: number
  format: string
  fileSize: number
}

export interface ProcessingStatus {
  isProcessing: boolean
  progress: number
  currentStep: string
}