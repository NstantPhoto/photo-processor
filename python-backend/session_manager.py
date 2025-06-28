from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import uuid
from enum import Enum


class SessionType(Enum):
    """Types of photography sessions"""
    WEDDING = "wedding"
    PORTRAIT = "portrait"
    SPORTS = "sports"
    EVENT = "event"
    PRODUCT = "product"
    LANDSCAPE = "landscape"
    CUSTOM = "custom"


@dataclass
class ProcessingPreset:
    """A saved processing preset for reuse"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pipeline_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class PhotoSession:
    """Represents a photography session with associated images and settings"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    date: datetime = field(default_factory=datetime.now)
    type: SessionType = SessionType.CUSTOM
    description: str = ""
    
    # Image tracking
    source_folder: Optional[Path] = None
    output_folder: Optional[Path] = None
    image_count: int = 0
    processed_count: int = 0
    images: List[Dict[str, Any]] = field(default_factory=list)
    
    # Processing settings
    pipeline_config: Dict[str, Any] = field(default_factory=dict)
    preset_id: Optional[str] = None
    
    # Metadata
    client_name: str = ""
    location: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    # Status
    status: str = "active"  # active, completed, archived
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Statistics
    processing_time_total: float = 0.0
    average_quality_score: float = 0.0
    culled_count: int = 0
    exported_count: int = 0


class SessionManager:
    """Manages photography sessions and processing presets"""
    
    def __init__(self, data_dir: Path = Path("data/sessions")):
        self.data_dir = data_dir
        self.sessions_dir = data_dir / "sessions"
        self.presets_dir = data_dir / "presets"
        
        # Create directories
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.presets_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache
        self._sessions: Dict[str, PhotoSession] = {}
        self._presets: Dict[str, ProcessingPreset] = {}
        
        # Load existing data
        self._load_sessions()
        self._load_presets()
    
    def create_session(self, name: str, session_type: SessionType, 
                      **kwargs) -> PhotoSession:
        """Create a new photo session"""
        session = PhotoSession(
            name=name,
            type=session_type,
            **kwargs
        )
        
        # Save session
        self._sessions[session.id] = session
        self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[PhotoSession]:
        """Get a session by ID"""
        return self._sessions.get(session_id)
    
    def list_sessions(self, status: Optional[str] = None,
                     session_type: Optional[SessionType] = None) -> List[PhotoSession]:
        """List all sessions with optional filtering"""
        sessions = list(self._sessions.values())
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        if session_type:
            sessions = [s for s in sessions if s.type == session_type]
        
        # Sort by date, newest first
        sessions.sort(key=lambda s: s.date, reverse=True)
        
        return sessions
    
    def update_session(self, session_id: str, **updates) -> Optional[PhotoSession]:
        """Update session properties"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.now()
        
        # Save changes
        self._save_session(session)
        
        return session
    
    def add_image_to_session(self, session_id: str, image_info: Dict[str, Any]):
        """Add an image to a session"""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        session.images.append(image_info)
        session.image_count = len(session.images)
        session.updated_at = datetime.now()
        
        self._save_session(session)
    
    def mark_image_processed(self, session_id: str, image_path: str, 
                           processing_time: float = 0.0,
                           quality_score: Optional[float] = None):
        """Mark an image as processed"""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        session.processed_count += 1
        session.processing_time_total += processing_time
        
        # Update average quality score
        if quality_score is not None:
            if session.average_quality_score == 0:
                session.average_quality_score = quality_score
            else:
                # Running average
                n = session.processed_count
                session.average_quality_score = (
                    (session.average_quality_score * (n - 1) + quality_score) / n
                )
        
        session.updated_at = datetime.now()
        self._save_session(session)
    
    def complete_session(self, session_id: str):
        """Mark a session as completed"""
        session = self._sessions.get(session_id)
        if not session:
            return
        
        session.status = "completed"
        session.completed_at = datetime.now()
        session.updated_at = datetime.now()
        
        self._save_session(session)
    
    def create_preset(self, name: str, pipeline_config: Dict[str, Any],
                     **kwargs) -> ProcessingPreset:
        """Create a new processing preset"""
        preset = ProcessingPreset(
            name=name,
            pipeline_config=pipeline_config,
            **kwargs
        )
        
        self._presets[preset.id] = preset
        self._save_preset(preset)
        
        return preset
    
    def get_preset(self, preset_id: str) -> Optional[ProcessingPreset]:
        """Get a preset by ID"""
        return self._presets.get(preset_id)
    
    def list_presets(self, tags: Optional[List[str]] = None) -> List[ProcessingPreset]:
        """List all presets with optional tag filtering"""
        presets = list(self._presets.values())
        
        if tags:
            # Filter by tags (any match)
            presets = [p for p in presets if any(tag in p.tags for tag in tags)]
        
        # Sort by name
        presets.sort(key=lambda p: p.name)
        
        return presets
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a session"""
        session = self._sessions.get(session_id)
        if not session:
            return {}
        
        return {
            'total_images': session.image_count,
            'processed_images': session.processed_count,
            'completion_percentage': (session.processed_count / session.image_count * 100) 
                                   if session.image_count > 0 else 0,
            'culled_images': session.culled_count,
            'exported_images': session.exported_count,
            'average_quality_score': session.average_quality_score,
            'total_processing_time': session.processing_time_total,
            'average_processing_time': (session.processing_time_total / session.processed_count) 
                                     if session.processed_count > 0 else 0,
            'status': session.status,
            'duration': (session.completed_at - session.created_at).total_seconds() 
                       if session.completed_at else None
        }
    
    def _save_session(self, session: PhotoSession):
        """Save session to disk"""
        session_file = self.sessions_dir / f"{session.id}.json"
        
        # Convert to dict for JSON serialization
        session_dict = {
            'id': session.id,
            'name': session.name,
            'date': session.date.isoformat(),
            'type': session.type.value,
            'description': session.description,
            'source_folder': str(session.source_folder) if session.source_folder else None,
            'output_folder': str(session.output_folder) if session.output_folder else None,
            'image_count': session.image_count,
            'processed_count': session.processed_count,
            'images': session.images,
            'pipeline_config': session.pipeline_config,
            'preset_id': session.preset_id,
            'client_name': session.client_name,
            'location': session.location,
            'tags': session.tags,
            'notes': session.notes,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'processing_time_total': session.processing_time_total,
            'average_quality_score': session.average_quality_score,
            'culled_count': session.culled_count,
            'exported_count': session.exported_count
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_dict, f, indent=2)
    
    def _save_preset(self, preset: ProcessingPreset):
        """Save preset to disk"""
        preset_file = self.presets_dir / f"{preset.id}.json"
        
        preset_dict = {
            'id': preset.id,
            'name': preset.name,
            'description': preset.description,
            'pipeline_config': preset.pipeline_config,
            'created_at': preset.created_at.isoformat(),
            'updated_at': preset.updated_at.isoformat(),
            'tags': preset.tags
        }
        
        with open(preset_file, 'w') as f:
            json.dump(preset_dict, f, indent=2)
    
    def _load_sessions(self):
        """Load sessions from disk"""
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                
                # Convert back to PhotoSession
                session = PhotoSession(
                    id=data['id'],
                    name=data['name'],
                    date=datetime.fromisoformat(data['date']),
                    type=SessionType(data['type']),
                    description=data.get('description', ''),
                    source_folder=Path(data['source_folder']) if data.get('source_folder') else None,
                    output_folder=Path(data['output_folder']) if data.get('output_folder') else None,
                    image_count=data.get('image_count', 0),
                    processed_count=data.get('processed_count', 0),
                    images=data.get('images', []),
                    pipeline_config=data.get('pipeline_config', {}),
                    preset_id=data.get('preset_id'),
                    client_name=data.get('client_name', ''),
                    location=data.get('location', ''),
                    tags=data.get('tags', []),
                    notes=data.get('notes', ''),
                    status=data.get('status', 'active'),
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at']),
                    completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
                    processing_time_total=data.get('processing_time_total', 0.0),
                    average_quality_score=data.get('average_quality_score', 0.0),
                    culled_count=data.get('culled_count', 0),
                    exported_count=data.get('exported_count', 0)
                )
                
                self._sessions[session.id] = session
                
            except Exception as e:
                print(f"Error loading session {session_file}: {e}")
    
    def _load_presets(self):
        """Load presets from disk"""
        for preset_file in self.presets_dir.glob("*.json"):
            try:
                with open(preset_file, 'r') as f:
                    data = json.load(f)
                
                preset = ProcessingPreset(
                    id=data['id'],
                    name=data['name'],
                    description=data.get('description', ''),
                    pipeline_config=data['pipeline_config'],
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at']),
                    tags=data.get('tags', [])
                )
                
                self._presets[preset.id] = preset
                
            except Exception as e:
                print(f"Error loading preset {preset_file}: {e}")
    
    def get_default_presets(self) -> Dict[str, ProcessingPreset]:
        """Get default presets for common photography types"""
        defaults = {
            'wedding': ProcessingPreset(
                name="Wedding - Bright & Airy",
                description="Light, bright processing for wedding photos",
                pipeline_config={
                    'nodes': {
                        'exposure': {'auto_mode': True, 'preserve_highlights': True},
                        'brightness': {'brightness': 10, 'preserve_contrast': True},
                        'color_balance': {'temperature': 10, 'tint': 5, 'preserve_skin_tones': True},
                        'contrast': {'contrast': -10, 'algorithm': 'sigmoid'}
                    }
                },
                tags=['wedding', 'bright', 'airy']
            ),
            'portrait': ProcessingPreset(
                name="Portrait - Natural Skin",
                description="Natural skin tones with subtle enhancement",
                pipeline_config={
                    'nodes': {
                        'exposure': {'auto_mode': True},
                        'color_balance': {'auto_mode': True, 'preserve_skin_tones': True},
                        'contrast': {'contrast': 5, 'algorithm': 'clahe'}
                    }
                },
                tags=['portrait', 'natural', 'skin']
            ),
            'sports': ProcessingPreset(
                name="Sports - High Impact",
                description="High contrast and vibrant colors for sports",
                pipeline_config={
                    'nodes': {
                        'exposure': {'auto_mode': True},
                        'contrast': {'contrast': 30, 'algorithm': 'linear'},
                        'color_balance': {'temperature': -5, 'tint': 0}
                    }
                },
                tags=['sports', 'action', 'vibrant']
            )
        }
        
        return defaults