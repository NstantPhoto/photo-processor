# DEVELOPMENT_RULES.md

Strict boundaries and guidelines for all Nstant Nfinity development.

## NEVER DO

1. **Modify working code without explicit permission**
   - Always ask before refactoring
   - Document why changes are needed
   - Keep working backups

2. **Add new npm/pip packages without approval**
   - Every dependency increases bundle size
   - Security implications must be reviewed
   - Check for lighter alternatives first

3. **Change established file structures**
   - Consistency is critical for team development
   - Migration requires planning

4. **Implement features beyond the current scope**
   - Stay focused on current sprint goals
   - Feature creep kills projects
   - Document ideas for future sprints

5. **Create circular dependencies**
   - Maintain clear module boundaries
   - Dependencies flow one direction
   - Use events/callbacks for reverse communication

6. **Skip error handling "for now"**
   - Every operation that can fail must have error handling
   - User-friendly error messages required
   - Log technical details for debugging

7. **Use synchronous file operations for images**
   - Always use async I/O for file operations
   - UI must remain responsive
   - Show progress for long operations

8. **Send image data through IPC**
   - Only send file paths between processes
   - Use memory-mapped files for large data
   - IPC is for control messages only

## ALWAYS DO

1. **Follow patterns in the examples/ directory**
   - Consistency across codebase
   - Proven patterns that work
   - Update examples when patterns evolve

2. **Check memory requirements before processing**
   ```python
   required_memory = image_width * image_height * 4 * 3  # RGB + processing overhead
   if required_memory > available_memory:
       use_tiled_processing()
   ```

3. **Include progress callbacks for operations >100ms**
   ```python
   async def process_image(image, progress_callback):
       progress_callback(0.1, "Starting")
       # ... processing ...
       progress_callback(1.0, "Complete")
   ```

4. **Write tests for new image processors**
   - Unit tests for core logic
   - Integration tests with sample images
   - Performance benchmarks

5. **Update PROJECT_STATE.md after each feature**
   - Mark completed items
   - Document any issues found
   - Update performance metrics

6. **Ask for clarification if requirements are ambiguous**
   - Better to ask than assume
   - Document clarifications in code comments
   - Update requirements docs

## WHEN UNCERTAIN

1. **Stop and ask for clarification**
   - Don't guess at requirements
   - Present options with pros/cons
   - Wait for decision before proceeding

2. **Refer to existing patterns**
   - Check similar implementations
   - Follow established conventions
   - Ask why if pattern seems wrong

3. **Check the architecture diagram**
   - Ensure changes align with overall design
   - Consider impact on other components
   - Maintain architectural integrity

4. **Consult the photography wisdom section**
   - Domain knowledge matters
   - Photographers have specific needs
   - Quality over speed for final output

## CODE QUALITY STANDARDS

### TypeScript/JavaScript
```typescript
// ALWAYS use TypeScript with strict mode
// ALWAYS use explicit types (no 'any')
// ALWAYS handle null/undefined
// ALWAYS use async/await over callbacks

// Good
async function processImage(path: string): Promise<ProcessedImage> {
  if (!path) throw new Error('Path required');
  try {
    const image = await loadImage(path);
    return await enhance(image);
  } catch (error) {
    logger.error('Processing failed', { path, error });
    throw new UserError('Failed to process image');
  }
}
```

### Python
```python
# ALWAYS use type hints
# ALWAYS follow PEP 8
# ALWAYS use dataclasses for data structures
# ALWAYS handle exceptions explicitly

# Good
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    success: bool
    output_path: Optional[str]
    error_message: Optional[str]
    processing_time: float

async def process_image(
    image_path: str,
    options: ProcessingOptions
) -> ProcessingResult:
    """Process image with given options.
    
    Args:
        image_path: Path to input image
        options: Processing configuration
        
    Returns:
        ProcessingResult with outcome details
    """
    if not os.path.exists(image_path):
        return ProcessingResult(
            success=False,
            output_path=None,
            error_message="File not found",
            processing_time=0.0
        )
```

### React Components
```typescript
// ALWAYS use functional components with hooks
// ALWAYS memo expensive components
// ALWAYS use proper TypeScript props
// NEVER use inline styles for complex styling

// Good
interface ImageNodeProps {
  id: string;
  data: ImageNodeData;
  selected: boolean;
  onUpdate: (id: string, data: Partial<ImageNodeData>) => void;
}

export const ImageNode = memo<ImageNodeProps>(({ 
  id, 
  data, 
  selected, 
  onUpdate 
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  
  const handleProcess = useCallback(async () => {
    setIsProcessing(true);
    try {
      await processImage(data.imagePath);
      onUpdate(id, { status: 'completed' });
    } catch (error) {
      onUpdate(id, { status: 'error', error: error.message });
    } finally {
      setIsProcessing(false);
    }
  }, [data.imagePath, id, onUpdate]);
  
  return (
    <div className={cn(
      'node-base',
      selected && 'selected',
      isProcessing && 'processing'
    )}>
      {/* Component content */}
    </div>
  );
});
```

## PERFORMANCE STANDARDS

1. **Preview Generation**
   - Must complete in <100ms
   - Use lower resolution (max 1920x1080)
   - Cache generated previews

2. **Memory Usage**
   - Never exceed 8GB for processing queue
   - Release memory immediately after use
   - Monitor memory in real-time

3. **UI Responsiveness**
   - 60fps during all operations
   - No blocking operations on main thread
   - Debounce expensive updates

4. **Batch Processing**
   - Process in parallel up to CPU count
   - Dynamic batch sizing based on resources
   - Progress reporting every 100ms

## TESTING REQUIREMENTS

1. **Coverage**
   - Minimum 80% for core processing logic
   - 100% for error handling paths
   - Integration tests for full pipeline

2. **Performance**
   - Benchmark every processor
   - Track regression in metrics
   - Test with various image sizes

3. **Memory**
   - Test with 100MP images
   - Verify no memory leaks
   - Test low-memory scenarios

## GIT COMMIT STANDARDS

```bash
# Format: <type>(<scope>): <subject>
# Types: feat, fix, docs, style, refactor, test, chore
# Scope: component or file affected
# Subject: imperative mood, lowercase

# Good examples:
feat(node-editor): add drag-and-drop support
fix(processor): handle corrupted EXIF data
docs(api): update endpoint documentation
test(culling): add face detection tests

# Include in commit body:
# - Why the change was needed
# - What the change does
# - Any breaking changes
```

## REMEMBER

> "Every line of code should answer: Does this help photographers spend less time at the computer and more time behind the camera?"

This is our north star. If a feature doesn't clearly support this goal, reconsider its priority.