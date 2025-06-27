import { create } from 'zustand'
import type { ImageInfo } from '../types/image'

interface ImageStore {
  currentImage: ImageInfo | null
  setCurrentImage: (image: ImageInfo | null) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
}

export const useImageStore = create<ImageStore>((set) => ({
  currentImage: null,
  setCurrentImage: (image) => set({ currentImage: image }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}))