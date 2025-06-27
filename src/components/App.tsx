import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'
import { ImageViewer } from './ImageViewer'
import { HotFolderPanel } from './HotFolderPanel'
import { useImageStore } from '../stores/imageStore'
import type { ImageInfo } from '../types/image'

function App() {
  const { setCurrentImage, setIsLoading } = useImageStore()
  const [error, setError] = useState<string | null>(null)
  const [backendHealthy, setBackendHealthy] = useState(false)
  const [checkingBackend, setCheckingBackend] = useState(true)

  useEffect(() => {
    // Check backend health on startup
    const checkHealth = async () => {
      try {
        const healthy = await invoke<boolean>('check_backend_health')
        setBackendHealthy(healthy)
        if (!healthy) {
          setError('Python processing engine is not running. Please start it with: python -m uvicorn python-backend.main:app --port 8888')
        }
      } catch (err) {
        setBackendHealthy(false)
        setError('Failed to check backend status')
      } finally {
        setCheckingBackend(false)
      }
    }

    checkHealth()
    // Check every 5 seconds
    const interval = setInterval(checkHealth, 5000)
    return () => clearInterval(interval)
  }, [])

  const handleOpenImage = async () => {
    try {
      setError(null)
      setIsLoading(true)

      // Open file dialog
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Images',
          extensions: ['png', 'jpg', 'jpeg', 'webp', 'bmp']
        }]
      })

      if (selected && typeof selected === 'string') {
        // Get image info from backend
        const imageInfo = await invoke<ImageInfo>('get_image_info', { path: selected })
        setCurrentImage(imageInfo)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to open image')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      <header className="bg-gray-800 p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">
            Nstant Nfinity - Photo Processor
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${backendHealthy ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-300">
                {checkingBackend ? 'Checking...' : backendHealthy ? 'Engine Ready' : 'Engine Offline'}
              </span>
            </div>
            <button
              onClick={handleOpenImage}
              disabled={!backendHealthy}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            >
              Open Image
            </button>
          </div>
        </div>
        {error && (
          <div className="mt-2 text-red-400 text-sm">{error}</div>
        )}
      </header>
      <main className="flex-1 overflow-hidden flex">
        <div className="flex-1">
          <ImageViewer />
        </div>
        <div className="w-96 p-4 bg-gray-850 border-l border-gray-700">
          <HotFolderPanel />
        </div>
      </main>
    </div>
  )
}

export default App