import React from 'react';
import { Folder, Camera, Sparkles, Sliders, Image, Download, Wand2, Palette, Crop } from 'lucide-react';
import './NodePalette.css';

interface NodeType {
  type: string;
  label: string;
  icon: React.ReactNode;
  processorType: string;
  category: string;
}

const nodeTypes: NodeType[] = [
  // Input nodes
  { type: 'input', label: 'Hot Folder', icon: <Folder size={20} />, processorType: 'hot_folder', category: 'Input' },
  { type: 'input', label: 'Manual Import', icon: <Camera size={20} />, processorType: 'manual_import', category: 'Input' },
  
  // Analysis nodes
  { type: 'processor', label: 'AI Analysis', icon: <Sparkles size={20} />, processorType: 'ai_analysis', category: 'Analysis' },
  { type: 'processor', label: 'Quality Check', icon: <Sliders size={20} />, processorType: 'quality_check', category: 'Analysis' },
  
  // Correction nodes
  { type: 'processor', label: 'Exposure', icon: <Sliders size={20} />, processorType: 'exposure', category: 'Corrections' },
  { type: 'processor', label: 'Color Balance', icon: <Palette size={20} />, processorType: 'color_balance', category: 'Corrections' },
  { type: 'processor', label: 'Brightness', icon: <Sliders size={20} />, processorType: 'brightness', category: 'Corrections' },
  { type: 'processor', label: 'Contrast', icon: <Sliders size={20} />, processorType: 'contrast', category: 'Corrections' },
  
  // Creative nodes
  { type: 'processor', label: 'Color Grading', icon: <Palette size={20} />, processorType: 'color_grading', category: 'Creative' },
  { type: 'processor', label: 'Background Removal', icon: <Wand2 size={20} />, processorType: 'bg_removal', category: 'Creative' },
  
  // Utility nodes
  { type: 'processor', label: 'Resize', icon: <Crop size={20} />, processorType: 'resize', category: 'Utility' },
  { type: 'processor', label: 'Watermark', icon: <Image size={20} />, processorType: 'watermark', category: 'Utility' },
  
  // Output nodes
  { type: 'output', label: 'Export', icon: <Download size={20} />, processorType: 'export', category: 'Output' },
];

const categories = ['Input', 'Analysis', 'Corrections', 'Creative', 'Utility', 'Output'];

export const NodePalette: React.FC = () => {
  const onDragStart = (event: React.DragEvent, nodeType: NodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType.type);
    event.dataTransfer.setData('processorType', nodeType.processorType);
    event.dataTransfer.setData('processorName', nodeType.label);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="node-palette">
      <h3 className="node-palette-title">Processing Nodes</h3>
      <div className="node-palette-content">
        {categories.map((category) => (
          <div key={category} className="node-category">
            <h4 className="node-category-title">{category}</h4>
            <div className="node-category-items">
              {nodeTypes
                .filter((node) => node.category === category)
                .map((node) => (
                  <div
                    key={node.processorType}
                    className={`node-palette-item node-type-${node.type}`}
                    onDragStart={(event) => onDragStart(event, node)}
                    draggable
                  >
                    <div className="node-icon">{node.icon}</div>
                    <span className="node-label">{node.label}</span>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};