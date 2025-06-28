import React, { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Settings, ChevronDown, ChevronUp } from 'lucide-react';

interface ProcessingNodeData {
  label: string;
  processorType: string;
  parameters?: Record<string, any>;
  onParameterChange?: (params: Record<string, any>) => void;
}

const ProcessingNode: React.FC<NodeProps<ProcessingNodeData>> = ({ data, selected }) => {
  const [showParams, setShowParams] = useState(false);
  const [params, setParams] = useState(data.parameters || {});

  const handleParameterChange = (key: string, value: any) => {
    const newParams = { ...params, [key]: value };
    setParams(newParams);
    data.onParameterChange?.(newParams);
  };

  const renderParameters = () => {
    switch (data.processorType) {
      case 'exposure':
        return (
          <>
            <div className="space-y-2">
              <div>
                <label className="text-xs text-gray-400">Exposure</label>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={params.exposure || 0}
                  onChange={(e) => handleParameterChange('exposure', Number(e.target.value))}
                  className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="text-xs text-right text-cyan-400 mt-1">
                  {params.exposure || 0}
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-400">Brightness</label>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={params.brightness || 0}
                  onChange={(e) => handleParameterChange('brightness', Number(e.target.value))}
                  className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                />
                <div className="text-xs text-right text-cyan-400 mt-1">
                  {params.brightness || 0}
                </div>
              </div>
            </div>
          </>
        );
      
      case 'color_balance':
        return (
          <div className="space-y-2">
            <div>
              <label className="text-xs text-gray-400">Temperature</label>
              <input
                type="range"
                min="-100"
                max="100"
                value={params.temperature || 0}
                onChange={(e) => handleParameterChange('temperature', Number(e.target.value))}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="text-xs text-right text-cyan-400 mt-1">
                {params.temperature || 0}
              </div>
            </div>
            <div>
              <label className="text-xs text-gray-400">Tint</label>
              <input
                type="range"
                min="-100"
                max="100"
                value={params.tint || 0}
                onChange={(e) => handleParameterChange('tint', Number(e.target.value))}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
              />
              <div className="text-xs text-right text-cyan-400 mt-1">
                {params.tint || 0}
              </div>
            </div>
          </div>
        );
      
      case 'denoise':
        return (
          <div>
            <label className="text-xs text-gray-400">Strength</label>
            <input
              type="range"
              min="0"
              max="100"
              value={params.strength || 50}
              onChange={(e) => handleParameterChange('strength', Number(e.target.value))}
              className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="text-xs text-right text-cyan-400 mt-1">
              {params.strength || 50}%
            </div>
          </div>
        );
      
      case 'resize':
        return (
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-400">Width</label>
                <input
                  type="number"
                  value={params.width || 1920}
                  onChange={(e) => handleParameterChange('width', Number(e.target.value))}
                  className="w-full px-2 py-1 text-xs bg-black/40 border border-white/20 rounded text-white"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400">Height</label>
                <input
                  type="number"
                  value={params.height || 1080}
                  onChange={(e) => handleParameterChange('height', Number(e.target.value))}
                  className="w-full px-2 py-1 text-xs bg-black/40 border border-white/20 rounded text-white"
                />
              </div>
            </div>
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={params.maintainAspect !== false}
                onChange={(e) => handleParameterChange('maintainAspect', e.target.checked)}
                className="rounded border-gray-600"
              />
              Maintain aspect ratio
            </label>
          </div>
        );
      
      default:
        return (
          <div className="text-xs text-gray-500 italic">
            No parameters available
          </div>
        );
    }
  };

  const hasParameters = ['exposure', 'color_balance', 'denoise', 'resize'].includes(data.processorType);

  return (
    <div
      className={`
        relative min-w-[220px] backdrop-blur-md bg-black/40 
        border-2 rounded-lg transition-all duration-200
        ${selected 
          ? 'border-cyan-500 shadow-[0_0_20px_rgba(0,212,255,0.5)]' 
          : 'border-white/20 hover:border-cyan-500/50'
        }
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Settings className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-medium text-white">{data.label}</h3>
        </div>
        {hasParameters && (
          <button
            onClick={() => setShowParams(!showParams)}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            {showParams ? (
              <ChevronUp className="w-4 h-4 text-gray-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-400" />
            )}
          </button>
        )}
      </div>

      {/* Parameters */}
      {showParams && hasParameters && (
        <div className="p-3 border-b border-white/10">
          {renderParameters()}
        </div>
      )}

      {/* Status */}
      <div className="p-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400">Status</span>
          <span className="text-green-400">Ready</span>
        </div>
      </div>

      {/* Gradient border effect */}
      {selected && (
        <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-cyan-500/20 to-blue-500/20 pointer-events-none" />
      )}

      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-3 !h-3 !bg-red-500 !border-2 !border-gray-900"
        style={{ left: -7 }}
      />

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-3 !h-3 !bg-cyan-500 !border-2 !border-gray-900"
        style={{ right: -7 }}
      />
    </div>
  );
};

export default memo(ProcessingNode);