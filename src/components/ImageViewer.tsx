import { motion } from 'framer-motion'
import { useImageStore } from '../stores/imageStore'
import { convertFileSrc } from '@tauri-apps/api/core'

export function ImageViewer() {
  const { currentImage, isLoading } = useImageStore()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full"
        />
      </div>
    )
  }

  if (!currentImage) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <p>No image loaded. Click "Open Image" to get started.</p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="flex items-center justify-center h-full p-4"
    >
      <img
        src={convertFileSrc(currentImage.path)}
        alt="Current"
        className="max-w-full max-h-full object-contain rounded-lg shadow-2xl"
      />
      <div className="absolute bottom-4 left-4 bg-black bg-opacity-50 text-white p-2 rounded">
        <p className="text-sm">
          {currentImage.width} × {currentImage.height} • {currentImage.format}
        </p>
      </div>
    </motion.div>
  )
}