# DEVELOPMENT_WORKFLOW.md

Enforces incremental development for Nstant Nfinity. Follow this EXACT sequence for EVERY feature.

## The 5-Phase Development Cycle

For EVERY new feature, follow these phases in order. NEVER skip steps.

### Phase 1: REVIEW
**Time: 15-30 minutes**

Before writing any code:

1. **Read Current State**
   ```bash
   # Start every session by reading:
   cat PROJECT_STATE.md | grep "CURRENT SPRINT"
   cat PROJECT_STATE.md | grep "Blockers"
   ```

2. **Review Related Code**
   - Find similar features already implemented
   - Understand existing patterns
   - Check for reusable components

3. **Confirm Understanding**
   - State the task in your own words
   - List expected inputs/outputs
   - Identify potential edge cases
   - If unclear, STOP and ask for clarification

**Exit Criteria:**
- [ ] Can explain the feature's purpose
- [ ] Know which files will be affected
- [ ] Have identified similar patterns in codebase

### Phase 2: DESIGN
**Time: 30-60 minutes**

Design before implementing:

1. **Write Interface/Types First**
   ```typescript
   // Start with the API contract
   interface ImageProcessor {
     name: string;
     process(image: ImageData): Promise<ImageData>;
     estimateMemory(dimensions: ImageDimensions): number;
   }
   ```

2. **Create Stub Implementation**
   ```python
   class ExposureCorrector(BaseProcessor):
       """Corrects image exposure automatically"""
       
       def process(self, image: np.ndarray) -> np.ndarray:
           # TODO: Implement
           raise NotImplementedError()
           
       def estimate_memory(self, shape: Tuple[int, int, int]) -> int:
           # TODO: Calculate actual requirements
           return shape[0] * shape[1] * shape[2] * 4
   ```

3. **Get Design Approval**
   - Show interface design
   - Explain integration points
   - Discuss any architectural concerns
   - **WAIT for approval before proceeding**

**Exit Criteria:**
- [ ] Interfaces defined with full types
- [ ] Stub implementation compiles/runs
- [ ] Design approved or feedback incorporated

### Phase 3: IMPLEMENTATION
**Time: 2-4 hours per component**

Build incrementally:

1. **Start with Core Logic**
   ```python
   def correct_exposure(self, image: np.ndarray, target_ev: float) -> np.ndarray:
       # Implement one piece at a time
       # First: basic correction
       corrected = image * (2 ** target_ev)
       return np.clip(corrected, 0, 255).astype(np.uint8)
   ```

2. **Add Tests Immediately**
   ```python
   def test_exposure_correction_brightens():
       # Test BEFORE adding more features
       dark_image = np.ones((100, 100, 3)) * 50
       bright = correct_exposure(dark_image, 1.0)
       assert bright.mean() > dark_image.mean()
   ```

3. **Iterate in Small Steps**
   - Implement one method
   - Test it works
   - Commit working state
   - Add next method
   - **Never write >50 lines without testing**

4. **Handle Errors Early**
   ```python
   if image.size == 0:
       raise ValueError("Empty image")
   if not -5 <= target_ev <= 5:
       raise ValueError(f"Invalid EV adjustment: {target_ev}")
   ```

**Exit Criteria:**
- [ ] All methods implemented
- [ ] All tests passing
- [ ] Error cases handled
- [ ] Code follows style guide

### Phase 4: INTEGRATION
**Time: 1-2 hours**

Connect to existing systems:

1. **Wire Up to UI**
   ```typescript
   // Add to node registry
   const nodeTypes = {
     ...existingNodes,
     exposureCorrection: ExposureCorrectionNode
   };
   ```

2. **Connect to Backend**
   ```python
   # Register processor
   PROCESSORS['exposure'] = ExposureCorrector()
   ```

3. **Update Documentation**
   - Add to node type list
   - Document settings/parameters
   - Include usage examples

4. **Run Integration Tests**
   ```bash
   # Test full pipeline
   npm run test:e2e -- --grep "exposure correction"
   pytest tests/integration/test_full_pipeline.py
   ```

**Exit Criteria:**
- [ ] Feature accessible from UI
- [ ] Backend processing works
- [ ] Integration tests pass
- [ ] Documentation updated

### Phase 5: CHECKPOINT
**Time: 30 minutes**

Review and document:

1. **Update PROJECT_STATE.md**
   ```markdown
   ## COMPLETED COMPONENTS
   
   ### Exposure Correction
   - [x] Exposure Correction v1.0
     - Path: `/python-backend/processors/exposure.py`
     - Description: AI-powered exposure correction with highlight preservation
     - Test Status: 15/15 passing
     - Performance: 50ms for 25MP image
     - Version: 1.0
     - Last Updated: 2024-01-20
   ```

2. **Performance Check**
   ```bash
   # Run benchmarks
   python benchmark_suite.py --processor exposure
   # Must meet: <500ms for 25MP image
   ```

3. **Memory Check**
   ```python
   # Verify no memory leaks
   python -m memory_profiler test_processor.py
   ```

4. **Summarize Work**
   - What was built
   - Any issues encountered
   - Performance metrics
   - Next steps

**Exit Criteria:**
- [ ] PROJECT_STATE.md updated
- [ ] Performance benchmarks met
- [ ] No memory leaks
- [ ] Ready for next feature

## Example Workflow

**Task: Implement Noise Reduction Node**

### Phase 1: REVIEW (20 min)
- Read noise reduction requirements
- Review existing sharpening node (similar)
- Understand AI denoising models

### Phase 2: DESIGN (45 min)
```python
class NoiseReductionProcessor(BaseProcessor):
    def __init__(self, model_path: str):
        self.model = self.load_model(model_path)
        
    def estimate_memory(self, shape: Tuple[int, int, int]) -> int:
        # Model needs 200MB + image size * 4
        return 200 * 1024 * 1024 + (shape[0] * shape[1] * shape[2] * 4)
        
    def process_preview(self, image: np.ndarray) -> np.ndarray:
        # Fast preview using downscaled image
        pass
        
    def process_full(self, image: np.ndarray) -> np.ndarray:
        # Full quality using AI model
        pass
```

### Phase 3: IMPLEMENTATION (3 hours)
- Hour 1: Core denoising algorithm
- Hour 2: Preview generation
- Hour 3: Tests and error handling

### Phase 4: INTEGRATION (1.5 hours)
- Add to processor registry
- Create React node component  
- Wire up settings panel
- Test full pipeline

### Phase 5: CHECKPOINT (30 min)
- Update PROJECT_STATE.md
- Run benchmarks: 200ms ✓
- Memory usage: 450MB ✓
- Document in node list

## Sprint Planning

### Week Planning (Monday)
1. Review PROJECT_STATE.md priorities
2. Select 3-5 features for the week
3. Estimate time for each (use 5-phase estimates)
4. Update CURRENT SPRINT section

### Daily Planning
1. Pick 1-2 features maximum
2. Complete full 5-phase cycle
3. Don't start new feature if current isn't integrated

### End of Sprint (Friday)
1. Update all completed components
2. Run full test suite
3. Check performance benchmarks
4. Plan next sprint

## Common Pitfalls to Avoid

1. **"I'll add tests later"**
   - No. Tests in Phase 3, always.

2. **"Let me refactor this while I'm here"**
   - No. Stay focused on current feature.

3. **"This would be better if..."**
   - Document idea, stay on task.

4. **"I'll just implement these 5 features together"**
   - No. One feature, one cycle.

5. **"The design is obvious"**
   - Still do Phase 2. Always.

## Success Metrics

A feature is ONLY complete when:
- All 5 phases completed
- Tests passing (unit + integration)
- Performance benchmarks met
- Memory usage within limits
- Documentation updated
- PROJECT_STATE.md updated

## Remember

> "Slow is smooth, smooth is fast"

Following this workflow might feel slow initially, but it prevents:
- Massive refactors
- Mysterious bugs
- Performance regressions
- Forgotten features
- Technical debt

Trust the process. One phase at a time.