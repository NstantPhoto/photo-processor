import { create } from 'zustand'
import type { ImageInfo } from '../types/image'

interface ImageStore {
  currentImage: ImageInfo | null
  setCurrentImage: (image: ImageInfo | null) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
  images: ImageInfo[]
  selectedImages: string[]
  setImages: (images: ImageInfo[]) => void
  addImage: (image: ImageInfo) => void
  removeImage: (id: string) => void
  toggleImageSelection: (id: string) => void
  clearSelection: () => void
}

export const useImageStore = create<ImageStore>((set) => ({
  currentImage: null,
  setCurrentImage: (image) => set({ currentImage: image }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  images: [],
  selectedImages: [],
  setImages: (images) => set({ images }),
  addImage: (image) => set((state) => ({ images: [...state.images, image] })),
  removeImage: (id) => set((state) => ({ 
    images: state.images.filter(img => img.id !== id),
    selectedImages: state.selectedImages.filter(selectedId => selectedId !== id)
  })),
  toggleImageSelection: (id) => set((state) => ({
    selectedImages: state.selectedImages.includes(id)
      ? state.selectedImages.filter(selectedId => selectedId !== id)
      : [...state.selectedImages, id]
  })),
  clearSelection: () => set({ selectedImages: [] })
}))