import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Folder, CheckCircle, AlertCircle } from 'lucide-react';
import './nodes.css';

export interface InputNodeData {
  label: string;
  processorType: string;
  processorName: string;
  parameters: any;
  isProcessing: boolean;
  status?: 'ready' | 'processing' | 'error';
  fileCount?: number;
}

const InputNode: React.FC<NodeProps<InputNodeData>> = ({ data, selected }) => {
  const statusIcon = data.status === 'ready' ? 
    <CheckCircle size={16} className="status-icon ready" /> : 
    data.status === 'error' ? 
    <AlertCircle size={16} className="status-icon error" /> : null;

  return (
    <div className={`custom-node input-node ${selected ? 'selected' : ''} ${data.isProcessing ? 'processing' : ''}`}>
      <div className="node-header">
        <Folder size={20} />
        <span className="node-title">{data.label}</span>
        {statusIcon}
      </div>
      <div className="node-content">
        {data.fileCount !== undefined && (
          <div className="node-info">
            <span className="info-label">Files:</span>
            <span className="info-value">{data.fileCount}</span>
          </div>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        id="output"
        className="custom-handle source-handle"
      />
    </div>
  );
};

export default memo(InputNode);