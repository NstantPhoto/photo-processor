import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set, Tuple
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime
import networkx as nx

from .base_processor import BaseProcessor, ProcessingResult
from .memory_manager import MemoryManager
from .processing_queue import QueueItem, ProcessingStatus


logger = logging.getLogger(__name__)


@dataclass
class ProcessingNode:
    """Represents a node in the processing pipeline"""
    id: str
    processor: BaseProcessor
    inputs: List[str] = None  # IDs of input nodes
    outputs: List[str] = None  # IDs of output nodes
    parameters: Dict[str, Any] = None
    enabled: bool = True
    position: Tuple[float, float] = (0, 0)  # x, y position in UI
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.parameters is None:
            self.parameters = {}


class PipelineManager:
    """
    Manages the image processing pipeline execution.
    Handles node dependencies, parallel processing, and memory management.
    """
    
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize the pipeline manager.
        
        Args:
            memory_manager: Optional memory manager instance
        """
        self.memory_manager = memory_manager or MemoryManager()
        self.nodes: Dict[str, ProcessingNode] = {}
        self.graph = nx.DiGraph()
        self._processor_registry: Dict[str, type] = {}
        
    def register_processor(self, processor_type: str, processor_class: type):
        """
        Register a processor class for dynamic instantiation.
        
        Args:
            processor_type: Type identifier for the processor
            processor_class: The processor class
        """
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError(f"{processor_class} must inherit from BaseProcessor")
        
        self._processor_registry[processor_type] = processor_class
        logger.info(f"Registered processor: {processor_type}")
    
    def add_node(self, node: ProcessingNode):
        """
        Add a node to the pipeline.
        
        Args:
            node: Processing node to add
        """
        self.nodes[node.id] = node
        self.graph.add_node(node.id)
        
        # Update graph edges based on connections
        for input_id in node.inputs:
            if input_id in self.nodes:
                self.graph.add_edge(input_id, node.id)
        
        for output_id in node.outputs:
            if output_id in self.nodes:
                self.graph.add_edge(node.id, output_id)
        
        logger.debug(f"Added node: {node.id} ({node.processor.name})")
    
    def remove_node(self, node_id: str):
        """Remove a node from the pipeline."""
        if node_id in self.nodes:
            # Remove from graph
            self.graph.remove_node(node_id)
            
            # Update connections in other nodes
            for node in self.nodes.values():
                if node_id in node.inputs:
                    node.inputs.remove(node_id)
                if node_id in node.outputs:
                    node.outputs.remove(node_id)
            
            # Remove the node
            del self.nodes[node_id]
            logger.debug(f"Removed node: {node_id}")
    
    def connect_nodes(self, source_id: str, target_id: str):
        """
        Connect two nodes in the pipeline.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            raise ValueError("Both nodes must exist in the pipeline")
        
        # Update node connections
        if target_id not in self.nodes[source_id].outputs:
            self.nodes[source_id].outputs.append(target_id)
        if source_id not in self.nodes[target_id].inputs:
            self.nodes[target_id].inputs.append(source_id)
        
        # Update graph
        self.graph.add_edge(source_id, target_id)
        
        logger.debug(f"Connected: {source_id} -> {target_id}")
    
    def disconnect_nodes(self, source_id: str, target_id: str):
        """Disconnect two nodes."""
        if source_id in self.nodes and target_id in self.nodes[source_id].outputs:
            self.nodes[source_id].outputs.remove(target_id)
        
        if target_id in self.nodes and source_id in self.nodes[target_id].inputs:
            self.nodes[target_id].inputs.remove(source_id)
        
        if self.graph.has_edge(source_id, target_id):
            self.graph.remove_edge(source_id, target_id)
        
        logger.debug(f"Disconnected: {source_id} -> {target_id}")
    
    def validate_pipeline(self) -> Tuple[bool, List[str]]:
        """
        Validate the pipeline for cycles and other issues.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            errors.append("Pipeline contains cycles")
        
        # Check for disconnected nodes (except input nodes)
        for node_id, node in self.nodes.items():
            if not node.inputs and not any(
                node_id in other.inputs for other in self.nodes.values()
            ):
                # This might be an input node, which is okay
                if node.processor.processor_type != "input":
                    errors.append(f"Node {node_id} is disconnected")
        
        # Check for enabled path from input to output
        input_nodes = [n for n in self.nodes.values() 
                      if n.processor.processor_type == "input" and n.enabled]
        output_nodes = [n for n in self.nodes.values() 
                       if n.processor.processor_type == "output" and n.enabled]
        
        if not input_nodes:
            errors.append("No enabled input nodes")
        if not output_nodes:
            errors.append("No enabled output nodes")
        
        return len(errors) == 0, errors
    
    def get_execution_order(self) -> List[str]:
        """
        Get the order in which nodes should be executed.
        
        Returns:
            List of node IDs in execution order
        """
        try:
            # Get topological sort of enabled nodes
            enabled_subgraph = self.graph.subgraph(
                [n_id for n_id, n in self.nodes.items() if n.enabled]
            )
            return list(nx.topological_sort(enabled_subgraph))
        except nx.NetworkXError as e:
            logger.error(f"Failed to determine execution order: {e}")
            return []
    
    async def process_image(self, image_path: Path, 
                          output_path: Optional[Path] = None,
                          preview_only: bool = False) -> ProcessingResult:
        """
        Process an image through the pipeline.
        
        Args:
            image_path: Path to input image
            output_path: Optional output path
            preview_only: If True, only generate preview
            
        Returns:
            Final processing result
        """
        # Load image
        import cv2
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        # Check memory availability
        if not self.memory_manager.can_process_in_memory(image.shape):
            logger.warning(f"Image too large for memory, will use chunked processing")
            return await self._process_image_chunked(image, output_path, preview_only)
        
        # Get execution order
        execution_order = self.get_execution_order()
        if not execution_order:
            raise ValueError("No valid execution path in pipeline")
        
        # Process through pipeline
        results: Dict[str, ProcessingResult] = {}
        current_image = image
        
        for node_id in execution_order:
            node = self.nodes[node_id]
            
            # Skip disabled nodes
            if not node.enabled:
                continue
            
            # Get input image (from previous node or original)
            if node.inputs:
                # Use output from last input node
                last_input = node.inputs[-1]
                if last_input in results:
                    current_image = results[last_input].image
            
            # Process
            logger.debug(f"Processing with node: {node_id}")
            
            # Apply node parameters
            node.processor.set_parameters(**node.parameters)
            
            # Process image
            result = node.processor.process(current_image, preview_only)
            results[node_id] = result
            current_image = result.image
        
        # Save output if path provided
        if output_path and not preview_only:
            cv2.imwrite(str(output_path), current_image)
            logger.info(f"Saved processed image to: {output_path}")
        
        # Return final result
        final_result = list(results.values())[-1] if results else ProcessingResult(
            image=image,
            processing_time=0,
            metadata={}
        )
        
        return final_result
    
    async def _process_image_chunked(self, image: np.ndarray,
                                   output_path: Optional[Path],
                                   preview_only: bool) -> ProcessingResult:
        """Process large image in chunks."""
        # This is a placeholder for chunked processing
        # Will be implemented when we add tiled processing support
        logger.warning("Chunked processing not yet implemented, falling back to full image")
        return await self.process_image(image, output_path, preview_only)
    
    def save_pipeline(self, path: Path):
        """
        Save pipeline configuration to JSON.
        
        Args:
            path: Path to save the pipeline configuration
        """
        config = {
            "nodes": {},
            "processors": {}
        }
        
        # Save node configurations
        for node_id, node in self.nodes.items():
            config["nodes"][node_id] = {
                "processor_type": node.processor.processor_type,
                "processor_name": node.processor.name,
                "inputs": node.inputs,
                "outputs": node.outputs,
                "parameters": node.parameters,
                "enabled": node.enabled,
                "position": node.position
            }
            
            # Save processor parameters
            processor_key = f"{node.processor.processor_type}:{node.processor.name}"
            config["processors"][processor_key] = node.processor.get_parameters()
        
        # Write to file
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved pipeline configuration to: {path}")
    
    def load_pipeline(self, path: Path):
        """
        Load pipeline configuration from JSON.
        
        Args:
            path: Path to the pipeline configuration
        """
        with open(path, 'r') as f:
            config = json.load(f)
        
        # Clear existing pipeline
        self.nodes.clear()
        self.graph.clear()
        
        # Recreate nodes
        for node_id, node_config in config["nodes"].items():
            # Get processor class
            processor_type = node_config["processor_type"]
            if processor_type not in self._processor_registry:
                logger.warning(f"Unknown processor type: {processor_type}")
                continue
            
            # Create processor instance
            processor_class = self._processor_registry[processor_type]
            processor = processor_class(
                name=node_config["processor_name"],
                processor_type=processor_type
            )
            
            # Load processor parameters
            processor_key = f"{processor_type}:{node_config['processor_name']}"
            if processor_key in config.get("processors", {}):
                processor.set_parameters(**config["processors"][processor_key])
            
            # Create node
            node = ProcessingNode(
                id=node_id,
                processor=processor,
                inputs=node_config.get("inputs", []),
                outputs=node_config.get("outputs", []),
                parameters=node_config.get("parameters", {}),
                enabled=node_config.get("enabled", True),
                position=tuple(node_config.get("position", [0, 0]))
            )
            
            self.add_node(node)
        
        logger.info(f"Loaded pipeline configuration from: {path}")
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the current pipeline."""
        return {
            "node_count": len(self.nodes),
            "edge_count": self.graph.number_of_edges(),
            "is_valid": self.validate_pipeline()[0],
            "execution_order": self.get_execution_order(),
            "nodes": {
                node_id: {
                    "processor": node.processor.name,
                    "type": node.processor.processor_type,
                    "enabled": node.enabled,
                    "inputs": node.inputs,
                    "outputs": node.outputs
                }
                for node_id, node in self.nodes.items()
            }
        }