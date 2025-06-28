import { NodeTypes } from 'reactflow';
import InputNode from './nodes/InputNode';
import ProcessorNode from './nodes/ProcessorNode';
import OutputNode from './nodes/OutputNode';

export const nodeTypes: NodeTypes = {
  input: InputNode,
  processor: ProcessorNode,
  output: OutputNode,
};