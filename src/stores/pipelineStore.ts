import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { invoke } from '@tauri-apps/api/core';

interface PipelineNode {
  id: string;
  type: string;
  processorType: string;
  label: string;
  parameters: Record<string, any>;
  position: { x: number; y: number };
  enabled?: boolean;
}

interface PipelineConnection {
  source: string;
  target: string;
}

interface PipelineState {
  nodes: Map<string, PipelineNode>;
  connections: PipelineConnection[];
  isProcessing: boolean;
  currentProgress: number;
  processingQueue: string[];
  
  // Actions
  addNode: (node: PipelineNode) => void;
  removeNode: (nodeId: string) => void;
  updateNode: (nodeId: string, updates: Partial<PipelineNode>) => void;
  updateNodeParameters: (nodeId: string, parameters: Record<string, any>) => void;
  connectNodes: (source: string, target: string) => void;
  disconnectNodes: (source: string, target: string) => void;
  
  // Pipeline operations
  validatePipeline: () => Promise<{ valid: boolean; errors: string[] }>;
  savePipeline: (name: string) => Promise<void>;
  loadPipeline: (name: string) => Promise<void>;
  processBatch: (imagePaths: string[]) => Promise<void>;
  
  // Processing control
  startProcessing: () => void;
  stopProcessing: () => void;
  updateProgress: (progress: number) => void;
}

export const usePipelineStore = create<PipelineState>()(
  devtools(
    (set, get) => ({
      nodes: new Map(),
      connections: [],
      isProcessing: false,
      currentProgress: 0,
      processingQueue: [],

      addNode: (node) => set((state) => {
        const nodes = new Map(state.nodes);
        nodes.set(node.id, node);
        return { nodes };
      }),

      removeNode: (nodeId) => set((state) => {
        const nodes = new Map(state.nodes);
        nodes.delete(nodeId);
        
        // Remove related connections
        const connections = state.connections.filter(
          conn => conn.source !== nodeId && conn.target !== nodeId
        );
        
        return { nodes, connections };
      }),

      updateNode: (nodeId, updates) => set((state) => {
        const nodes = new Map(state.nodes);
        const node = nodes.get(nodeId);
        if (node) {
          nodes.set(nodeId, { ...node, ...updates });
        }
        return { nodes };
      }),

      updateNodeParameters: (nodeId, parameters) => set((state) => {
        const nodes = new Map(state.nodes);
        const node = nodes.get(nodeId);
        if (node) {
          nodes.set(nodeId, { ...node, parameters });
        }
        return { nodes };
      }),

      connectNodes: (source, target) => set((state) => {
        // Check if connection already exists
        const exists = state.connections.some(
          conn => conn.source === source && conn.target === target
        );
        
        if (!exists) {
          return { connections: [...state.connections, { source, target }] };
        }
        return state;
      }),

      disconnectNodes: (source, target) => set((state) => ({
        connections: state.connections.filter(
          conn => !(conn.source === source && conn.target === target)
        )
      })),

      validatePipeline: async () => {
        const state = get();
        const nodes = Array.from(state.nodes.values());
        
        try {
          const result = await invoke<{ valid: boolean; errors: string[] }>(
            'validate_pipeline',
            {
              nodes: nodes.map(node => ({
                id: node.id,
                processorType: node.processorType,
                parameters: node.parameters,
                enabled: node.enabled !== false
              })),
              connections: state.connections
            }
          );
          
          return result;
        } catch (error) {
          console.error('Failed to validate pipeline:', error);
          return { valid: false, errors: ['Failed to validate pipeline'] };
        }
      },

      savePipeline: async (name: string) => {
        const state = get();
        const nodes = Array.from(state.nodes.values());
        
        try {
          await invoke('save_pipeline', {
            name,
            pipeline: {
              nodes,
              connections: state.connections
            }
          });
        } catch (error) {
          console.error('Failed to save pipeline:', error);
          throw error;
        }
      },

      loadPipeline: async (name: string) => {
        try {
          const pipeline = await invoke<{
            nodes: PipelineNode[];
            connections: PipelineConnection[];
          }>('load_pipeline', { name });
          
          const nodes = new Map<string, PipelineNode>(
            pipeline.nodes.map((node: PipelineNode) => [node.id, node])
          );
          
          set({ nodes, connections: pipeline.connections });
        } catch (error) {
          console.error('Failed to load pipeline:', error);
          throw error;
        }
      },

      processBatch: async (imagePaths: string[]) => {
        const state = get();
        
        // Validate pipeline first
        const validation = await state.validatePipeline();
        if (!validation.valid) {
          throw new Error(`Pipeline validation failed: ${validation.errors.join(', ')}`);
        }
        
        set({ isProcessing: true, processingQueue: imagePaths, currentProgress: 0 });
        
        try {
          for (let i = 0; i < imagePaths.length; i++) {
            const path = imagePaths[i];
            
            // Process single image through pipeline
            await invoke('execute_pipeline', {
              pipelineConfig: {
                nodes: Array.from(state.nodes.values()).map(node => ({
                  id: node.id,
                  nodeType: node.type,
                  processorType: node.processorType,
                  parameters: node.parameters,
                  position: [node.position.x, node.position.y]
                })),
                connections: state.connections
              },
              inputPath: path,
              outputPath: path.replace(/\.(jpg|jpeg|png)$/i, '_processed.$1'),
              sessionId: null
            });
            
            // Update progress
            const progress = ((i + 1) / imagePaths.length) * 100;
            set({ currentProgress: progress });
          }
        } catch (error) {
          console.error('Processing failed:', error);
          throw error;
        } finally {
          set({ isProcessing: false, currentProgress: 0, processingQueue: [] });
        }
      },

      startProcessing: () => set({ isProcessing: true }),
      
      stopProcessing: () => set({ 
        isProcessing: false, 
        currentProgress: 0,
        processingQueue: [] 
      }),
      
      updateProgress: (progress) => set({ currentProgress: progress })
    }),
    {
      name: 'pipeline-store'
    }
  )
);