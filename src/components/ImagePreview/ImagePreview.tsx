import React, { useEffect, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import './ImagePreview.css';

interface PreviewResponse {
  preview_path: string;
  width: number;
  height: number;
  generation_time: number;
  cached: boolean;
}

interface ImagePreviewProps {
  imagePath: string;
  width?: number;
  height?: number;
  className?: string;
  onLoad?: () => void;
  onError?: (error: string) => void;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  imagePath,
  width = 800,
  height = 600,
  className = '',
  onLoad,
  onError
}) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const generatePreview = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await invoke<PreviewResponse>('generate_preview', {
          imagePath,
          width,
          height
        });

        if (!cancelled) {
          // Convert local path to Tauri asset URL
          const assetUrl = `asset://localhost/${response.preview_path}`;
          setPreviewUrl(assetUrl);
          setLoading(false);
          onLoad?.();
        }
      } catch (err) {
        if (!cancelled) {
          const errorMsg = err instanceof Error ? err.message : 'Failed to generate preview';
          setError(errorMsg);
          setLoading(false);
          onError?.(errorMsg);
        }
      }
    };

    generatePreview();

    return () => {
      cancelled = true;
    };
  }, [imagePath, width, height, onLoad, onError]);

  if (loading) {
    return (
      <div className={`image-preview-loading ${className}`}>
        <div className="loading-spinner" />
        <p>Generating preview...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`image-preview-error ${className}`}>
        <p>❌ {error}</p>
      </div>
    );
  }

  return (
    <div className={`image-preview ${className}`}>
      <img 
        src={previewUrl || ''} 
        alt="Preview"
        style={{ maxWidth: '100%', maxHeight: '100%' }}
      />
    </div>
  );
};