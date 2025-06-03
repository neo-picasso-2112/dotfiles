# Voice Assistant Enhancement - Product Requirements Document

## Executive Summary

This document outlines the enhancement of our existing voice assistant to integrate LiveKit Agents framework capabilities while maintaining our preferred RealtimeSTT for speech-to-text. The goal is to create a more responsive, production-ready voice-controlled coding assistant with native MCP (Model Context Protocol) server integration.

## Current State Analysis

### Existing Architecture
- **STT**: RealtimeSTT (Whisper-based, local processing)
- **LLM**: Claude via subprocess (calling `goose` CLI)
- **TTS**: Gemini 2.5 Flash TTS
- **Flow**: STT → Text → Claude Code → Text → TTS

### Current Strengths
- Fast local STT processing
- Direct Claude Code integration
- Simple architecture
- UV-based dependency management

### Current Pain Points
- No interruption handling
- Sequential processing (no streaming)
- Limited turn detection
- No MCP server tool integration
- Batch-style interactions

## Target Architecture

### Hybrid Approach Benefits
1. **Keep RealtimeSTT**: Maintain fast, local speech recognition
2. **Add LiveKit Components**: VAD, turn detection, streaming capabilities
3. **Native MCP Integration**: Direct access to Claude Code tools
4. **Streaming Pipeline**: Parallel STT/LLM/TTS processing
5. **Production Ready**: Scalable architecture for future deployment

### Technical Vision
```
[Audio Input] 
    ↓
[RealtimeSTT + LiveKit VAD] 
    ↓
[LiveKit Turn Detection] 
    ↓
[Claude Code MCP Tools] 
    ↓
[Streaming TTS Response]
```

## Feature Requirements

### Phase 1: Foundation Enhancement (Week 1-2)
- **FR-001**: Implement async/await patterns throughout codebase
- **FR-002**: Add proper streaming TTS with early audio start
- **FR-003**: Implement interruption detection and handling
- **FR-004**: Create modular STT interface for future LiveKit integration

### Phase 2: LiveKit Integration (Week 3-4)
- **FR-005**: Integrate LiveKit VAD (Voice Activity Detection)
- **FR-006**: Add LiveKit turn detection models
- **FR-007**: Implement LiveKit session management patterns
- **FR-008**: Create hybrid STT wrapper for RealtimeSTT + LiveKit

### Phase 3: MCP Tools Integration (Week 5-6)
- **FR-009**: Replace subprocess calls with native MCP integration
- **FR-010**: Implement `@function_tool` decorators for code operations
- **FR-011**: Add file system operations as MCP tools
- **FR-012**: Implement terminal command execution tools

### Phase 4: Production Readiness (Week 7-8)
- **FR-013**: Add conversation persistence and resume
- **FR-014**: Implement error handling and recovery
- **FR-015**: Add metrics and logging
- **FR-016**: Create deployment configuration

## Implementation Plan

### Phase 1: Foundation Enhancement

#### Task 1.1: Async Architecture Refactor
**Estimated Time**: 2 days
**Priority**: High

**Steps**:
1. Refactor `VoiceAIAssistant` class to use proper async patterns
2. Convert all blocking calls to async/await
3. Implement asyncio event loops properly
4. Update error handling for async operations

**Files to Modify**:
- `main.py` (current implementation)
- `reference/main.py`

**Acceptance Criteria**:
- All I/O operations are async
- No blocking calls in main thread
- Proper exception handling for async operations

#### Task 1.2: Streaming TTS Implementation
**Estimated Time**: 3 days
**Priority**: High

**Steps**:
1. Modify Gemini TTS to start playing audio before full generation
2. Implement audio chunk buffering
3. Add audio stream management
4. Test latency improvements

**Technical Details**:
```python
async def stream_tts(self, text: str):
    """Stream TTS audio chunks as they arrive"""
    audio_buffer = asyncio.Queue()
    
    # Start playback task
    playback_task = asyncio.create_task(self.play_audio_stream(audio_buffer))
    
    # Stream from Gemini
    async for chunk in self.gemini_tts_stream(text):
        await audio_buffer.put(chunk)
    
    await audio_buffer.put(None)  # End marker
    await playback_task
```

#### Task 1.3: Interruption Detection
**Estimated Time**: 2 days
**Priority**: Medium

**Steps**:
1. Add voice activity detection during TTS playback
2. Implement audio stream cancellation
3. Add graceful interruption handling
4. Test user experience improvements

### Phase 2: LiveKit Integration

#### Task 2.1: LiveKit Dependencies Setup
**Estimated Time**: 1 day
**Priority**: High

**Steps**:
1. Add LiveKit agents to dependencies
2. Update UV script metadata
3. Install and test LiveKit components
4. Configure development environment

**Dependencies to Add**:
```python
# Add to script dependencies
"livekit-agents[openai,silero,turn-detector,mcp]>=1.0",
"livekit-plugins-deepgram",
"livekit-plugins-elevenlabs"
```

#### Task 2.2: VAD Integration
**Estimated Time**: 2 days
**Priority**: High

**Steps**:
1. Initialize Silero VAD model
2. Integrate VAD with RealtimeSTT
3. Implement voice activity callbacks
4. Test voice detection accuracy

**Implementation**:
```python
from livekit.plugins import silero

class HybridSTT:
    def __init__(self):
        self.vad = silero.VAD.load()
        self.realtime_stt = AudioToTextRecorder(...)
        
    async def detect_speech(self, audio_chunk):
        is_speech = await self.vad.process(audio_chunk)
        if is_speech:
            return await self.realtime_stt.process(audio_chunk)
```

#### Task 2.3: Turn Detection Implementation
**Estimated Time**: 2 days
**Priority**: Medium

**Steps**:
1. Add English turn detection model
2. Implement turn boundary detection
3. Integrate with conversation flow
4. Test natural conversation patterns

### Phase 3: MCP Tools Integration

#### Task 3.1: MCP Tool Framework
**Estimated Time**: 3 days
**Priority**: High

**Steps**:
1. Create base MCP tool interface
2. Implement `@function_tool` decorator pattern
3. Add tool discovery and registration
4. Test tool execution framework

**Base Implementation**:
```python
from livekit.agents import function_tool, RunContext

@function_tool
async def edit_file(
    context: RunContext,
    file_path: str,
    old_content: str,
    new_content: str
) -> str:
    """Edit a file by replacing old content with new content"""
    # Implementation here
    return f"Successfully edited {file_path}"

@function_tool
async def read_file(
    context: RunContext,
    file_path: str
) -> str:
    """Read the contents of a file"""
    # Implementation here
    return file_content
```

#### Task 3.2: File System Tools
**Estimated Time**: 2 days
**Priority**: High

**Tools to Implement**:
- `read_file`: Read file contents
- `write_file`: Write file contents
- `edit_file`: Edit file with find/replace
- `list_files`: List directory contents
- `create_directory`: Create directories

#### Task 3.3: Terminal Command Tools
**Estimated Time**: 2 days
**Priority**: Medium

**Tools to Implement**:
- `run_command`: Execute shell commands
- `git_status`: Get git repository status
- `git_commit`: Commit changes
- `install_package`: Install Python packages

#### Task 3.4: Claude Code Integration
**Estimated Time**: 3 days
**Priority**: High

**Steps**:
1. Replace subprocess goose calls with direct MCP integration
2. Implement Claude Code tool interface
3. Add conversation context management
4. Test code generation and modification

### Phase 4: Production Readiness

#### Task 4.1: Session Management
**Estimated Time**: 2 days
**Priority**: Medium

**Features**:
- Conversation persistence
- Session resume capability
- Multi-user support preparation
- State management

#### Task 4.2: Error Handling & Recovery
**Estimated Time**: 2 days
**Priority**: High

**Features**:
- Graceful error recovery
- Audio device error handling
- Network connectivity issues
- Model availability fallbacks

#### Task 4.3: Logging & Metrics
**Estimated Time**: 1 day
**Priority**: Low

**Features**:
- Structured logging
- Performance metrics
- Usage analytics
- Debug information

## Technical Specifications

### Architecture Diagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Audio Input   │───▶│  RealtimeSTT +   │───▶│ LiveKit Turn    │
│                 │    │  LiveKit VAD     │    │ Detection       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐             │
│ Streaming TTS   │◀───│   Claude Code    │◀────────────┘
│   Response      │    │   MCP Tools      │
└─────────────────┘    └──────────────────┘
```

### Performance Requirements
- **STT Latency**: < 200ms for voice detection
- **Turn Detection**: < 100ms for natural interruptions
- **TTS Start**: < 500ms time-to-first-audio
- **Memory Usage**: < 2GB peak usage
- **CPU Usage**: < 50% on modern hardware

### Compatibility Requirements
- **Python**: 3.9+
- **Operating Systems**: macOS, Linux, Windows
- **Audio Devices**: Standard microphone/speakers
- **Dependencies**: UV package manager compatible

## Testing Strategy

### Unit Tests
- STT accuracy and latency
- VAD false positive/negative rates
- Turn detection accuracy
- MCP tool functionality

### Integration Tests
- End-to-end conversation flows
- Error recovery scenarios
- Performance benchmarks
- Multi-modal interactions

### User Acceptance Tests
- Natural conversation patterns
- Interruption handling
- Code modification accuracy
- Overall user experience

## Risk Assessment

### Technical Risks
1. **LiveKit Integration Complexity**: Medium risk
   - *Mitigation*: Phased approach, hybrid architecture
2. **Performance Degradation**: Low risk
   - *Mitigation*: Benchmarking at each phase
3. **Dependency Conflicts**: Medium risk
   - *Mitigation*: UV isolated environments

### Timeline Risks
1. **Learning Curve**: Medium risk
   - *Mitigation*: Dedicated research time
2. **Scope Creep**: High risk
   - *Mitigation*: Strict phase boundaries

## Success Metrics

### Phase 1 Success Criteria
- [ ] 50% reduction in response latency
- [ ] Interruption handling works 90% of the time
- [ ] No regression in STT accuracy

### Phase 2 Success Criteria
- [ ] VAD accuracy > 95%
- [ ] Turn detection latency < 100ms
- [ ] Maintains RealtimeSTT performance

### Phase 3 Success Criteria
- [ ] 100% MCP tool coverage for current features
- [ ] No subprocess dependencies
- [ ] Conversation context preserved

### Phase 4 Success Criteria
- [ ] Production deployment ready
- [ ] Error recovery rate > 95%
- [ ] Performance metrics within targets

## Resources Required

### Development Resources
- 1 Senior Developer (Architecture & Complex Integration)
- 1 Junior Developer (Implementation & Testing)
- 1 QA Engineer (Testing & Validation)

### Infrastructure
- Development machines with adequate audio hardware
- Test environments for different OS platforms
- LiveKit development server access

### Timeline
- **Total Duration**: 8 weeks
- **Phase 1**: Weeks 1-2
- **Phase 2**: Weeks 3-4
- **Phase 3**: Weeks 5-6
- **Phase 4**: Weeks 7-8

## Getting Started Guide for Junior Engineer

### Day 1: Environment Setup
1. Clone the repository
2. Review current architecture in `main.py` and `reference/main.py`
3. Set up development environment with UV
4. Run existing voice assistant to understand current behavior
5. Read LiveKit Agents documentation

### Day 2-3: Code Familiarization
1. Study RealtimeSTT integration patterns
2. Understand current TTS implementation
3. Trace conversation flow from voice input to response
4. Identify improvement opportunities

### Week 1 Focus
- Start with Task 1.1 (Async Architecture Refactor)
- Get familiar with asyncio patterns
- Create unit tests for current functionality
- Begin streaming TTS implementation

Remember: This is a complex integration project. Don't hesitate to ask questions and request code reviews frequently. Focus on one phase at a time and maintain the working state of the current system throughout development.