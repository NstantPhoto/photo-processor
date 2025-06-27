export interface ImageInfo {
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