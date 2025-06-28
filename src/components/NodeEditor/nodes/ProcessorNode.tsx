import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Sliders, Play, Pause } from 'lucide-react';
import './nodes.css';

export interface ProcessorNodeData {
  label: string;
  processorType: string;
  processorName: string;
  parameters: any;
  isProcessing: boolean;
  progress?: number;
  autoMode?: boolean;
}

const ProcessorNode: React.FC<NodeProps<ProcessorNodeData>> = ({ data, selected }) => {
  return (
    <div className={`custom-node processor-node ${selected ? 'selected' : ''} ${data.isProcessing ? 'processing' : ''}`}>
      <div className="node-header">
        <Sliders size={20} />
        <span className="node-title">{data.label}</span>
        {data.isProcessing ? <Pause size={16} /> : <Play size={16} />}
      </div>
      <div className="node-content">
        {data.autoMode !== undefined && (
          <div className="node-control">
            <label className="auto-mode-toggle">
              <input type="checkbox" checked={data.autoMode} readOnly />
              <span>Auto Mode</span>
            </label>
          </div>
        )}
        {data.progress !== undefined && data.isProcessing && (
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${data.progress * 100}%` }}
            />
          </div>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="custom-handle target-handle"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="custom-handle source-handle"
      />
    </div>
  );
};

export default memo(ProcessorNode);