import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Download, CheckCircle } from 'lucide-react';
import './nodes.css';

export interface OutputNodeData {
  label: string;
  processorType: string;
  processorName: string;
  parameters: any;
  isProcessing: boolean;
  exportCount?: number;
  format?: string;
}

const OutputNode: React.FC<NodeProps<OutputNodeData>> = ({ data, selected }) => {
  return (
    <div className={`custom-node output-node ${selected ? 'selected' : ''} ${data.isProcessing ? 'processing' : ''}`}>
      <div className="node-header">
        <Download size={20} />
        <span className="node-title">{data.label}</span>
        <CheckCircle size={16} className="status-icon ready" />
      </div>
      <div className="node-content">
        {data.format && (
          <div className="node-info">
            <span className="info-label">Format:</span>
            <span className="info-value">{data.format}</span>
          </div>
        )}
        {data.exportCount !== undefined && (
          <div className="node-info">
            <span className="info-label">Exported:</span>
            <span className="info-value">{data.exportCount}</span>
          </div>
        )}
      </div>
      <Handle
        type="target"
        position={Position.Left}
        id="input"
        className="custom-handle target-handle"
      />
    </div>
  );
};

export default memo(OutputNode);