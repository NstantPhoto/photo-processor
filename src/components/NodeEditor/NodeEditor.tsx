import React, { useCallback, useRef, useState, useEffect } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  useReactFlow,
  Controls,
  MiniMap,
  Background,
  Connection,
  Edge,
  Node,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { NodePalette } from './NodePalette';
import { nodeTypes } from './nodeTypes';
import { usePipelineStore } from '../../stores/pipelineStore';
import { useImageStore } from '../../stores/imageStore';
import type { ImageInfo } from '../../types/image';
import './NodeEditor.css';

const initialNodes: Node[] = [];
const initialEdges: Edge[] = [];

const NodeEditorContent: React.FC = () => {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const { project } = useReactFlow();
  
  const {
    nodes: pipelineNodes,
    isProcessing,
    currentProgress,
    addNode: addPipelineNode,
    removeNode: removePipelineNode,
    connectNodes: connectPipelineNodes,
    processBatch,
    validatePipeline
  } = usePipelineStore();
  
  const selectedImages = useImageStore((state) => state.selectedImages);
  const images = useImageStore((state) => state.images);

  // Sync React Flow nodes with pipeline store
  useEffect(() => {
    nodes.forEach(node => {
      const pipelineNode = {
        id: node.id,
        type: node.type || 'processor',
        processorType: node.data.processorType,
        label: node.data.label,
        parameters: node.data.parameters || {},
        position: { x: node.position.x, y: node.position.y },
        enabled: true
      };
      
      if (!pipelineNodes.has(node.id)) {
        addPipelineNode(pipelineNode);
      }
    });
    
    // Remove nodes that were deleted
    Array.from(pipelineNodes.keys()).forEach(nodeId => {
      if (!nodes.find(n => n.id === nodeId)) {
        removePipelineNode(nodeId);
      }
    });
  }, [nodes, pipelineNodes, addPipelineNode, removePipelineNode]);

  // Sync connections
  useEffect(() => {
    edges.forEach(edge => {
      connectPipelineNodes(edge.source, edge.target);
    });
  }, [edges, connectPipelineNodes]);

  const onConnect = useCallback(
    (params: Edge | Connection) => {
      const edge = {
        ...params,
        type: 'smoothstep',
        animated: true,
        style: { stroke: '#00d4ff', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#00d4ff',
        },
      };
      setEdges((eds: Edge[]) => addEdge(edge, eds));
    },
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');
      const processorType = event.dataTransfer.getData('processorType');
      const processorName = event.dataTransfer.getData('processorName');

      if (typeof type === 'undefined' || !type || !reactFlowBounds) {
        return;
      }

      const position = project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode: Node = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: { 
          label: processorName || `${type} node`,
          processorType,
          processorName,
          parameters: {},
          isProcessing: false,
        },
      };

      setNodes((nds: Node[]) => nds.concat(newNode));
    },
    [project, setNodes]
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id);
  }, []);

  const miniMapNodeColor = (node: Node) => {
    switch (node.type) {
      case 'input':
        return '#00d4ff';
      case 'processor':
        return '#ff3366';
      case 'output':
        return '#00ff88';
      default:
        return '#666';
    }
  };

  const handleProcessImages = async () => {
    if (selectedImages.length === 0) {
      alert('Please select images to process');
      return;
    }

    // Validate pipeline first
    const validation = await validatePipeline();
    if (!validation.valid) {
      alert(`Pipeline validation failed: ${validation.errors.join(', ')}`);
      return;
    }

    try {
      // Get paths of selected images
      const imagePaths = selectedImages.map((id: string) => {
        const image = images.find((img: ImageInfo) => img.id === id);
        return image?.path || '';
      }).filter((path: string) => path !== '');

      await processBatch(imagePaths);
      alert('Processing complete!');
    } catch (error) {
      console.error('Processing failed:', error);
      alert(`Processing failed: ${error}`);
    }
  };

  return (
    <div className="node-editor-container">
      <NodePalette />
      <div className="react-flow-wrapper" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          className="react-flow-glass"
        >
          <Background color="#333" gap={16} />
          <Controls className="react-flow-controls" />
          <MiniMap 
            nodeColor={miniMapNodeColor}
            className="react-flow-minimap"
            maskColor="rgba(0, 0, 0, 0.8)"
          />
        </ReactFlow>
      </div>
      {selectedNode && (
        <div className="node-properties-panel">
          <h3>Node Properties</h3>
          <p>Selected: {selectedNode}</p>
          {/* Add property controls here */}
        </div>
      )}
      
      {/* Floating Process Button */}
      {selectedImages.length > 0 && nodes.length > 0 && (
        <div className="process-button-container">
          <button 
            className={`process-button ${isProcessing ? 'processing' : ''}`}
            onClick={handleProcessImages}
            disabled={isProcessing}
          >
            {isProcessing ? (
              <>
                <span className="spinner"></span>
                Processing... {Math.round(currentProgress)}%
              </>
            ) : (
              <>Process {selectedImages.length} Images</>
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export const NodeEditor: React.FC = () => {
  return (
    <ReactFlowProvider>
      <NodeEditorContent />
    </ReactFlowProvider>
  );
};