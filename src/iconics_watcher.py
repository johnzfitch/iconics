"""
Iconics Watcher - Sophisticated File System Monitor

Event-driven icon ingestion with intelligent debouncing and coalescing.
Designed for future eBPF/AgentSight migration with clean event structures.
"""

import logging
import time
from collections import defaultdict
from pathlib import Path
from threading import Thread, Event as ThreadEvent
from typing import Dict, Optional, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object
    FileSystemEvent = object

from iconics_executive import IconicsExecutive, FileEvent
from iconics_output import OutputContext

logger = logging.getLogger(__name__)


class IconicsEventHandler(FileSystemEventHandler):
    """
    Handles file system events with intelligent debouncing.

    Implements a "settle period" pattern to coalesce rapid file operations
    (e.g., dragging 50 icons) into batch processing.
    """

    # Supported icon file extensions
    ICON_EXTENSIONS = {'.png', '.svg', '.webp', '.jpg', '.jpeg', '.ico', '.gif'}

    def __init__(self, watcher: 'IconicsWatcher'):
        """
        Initialize event handler.

        Args:
            watcher: Parent IconicsWatcher instance
        """
        super().__init__()
        self.watcher = watcher

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Filter by extension
        if path.suffix.lower() not in self.ICON_EXTENSIONS:
            return

        # Add to pending events with current timestamp
        self.watcher.register_event(path, 'created')

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Filter by extension
        if path.suffix.lower() not in self.ICON_EXTENSIONS:
            return

        # Add to pending events (will coalesce with created if rapid)
        self.watcher.register_event(path, 'modified')


class IconicsWatcher:
    """
    Sophisticated file watcher with debouncing and event coalescing.

    Architecture:
        OBSERVE (watchdog) → DEBOUNCE (settle period) → DECIDE (executive) → ACT (ingest)

    Features:
    - Intelligent debouncing: Waits for "quiet period" before processing
    - Event coalescing: Multiple rapid events on same file → single ingestion
    - Batch processing: Processes settled events in groups
    - Clean event structure: Ready for future eBPF migration
    """

    def __init__(
        self,
        executive: IconicsExecutive,
        watch_path: Path = Path('raw'),
        debounce_ms: int = 500,
        batch_size: int = 10
    ):
        """
        Initialize the watcher.

        Args:
            executive: IconicsExecutive instance for ingestion
            watch_path: Directory to monitor
            debounce_ms: Milliseconds to wait for "quiet period"
            batch_size: Maximum icons to process in one batch
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog package required for file watching. "
                "Install with: pip install watchdog"
            )

        self.executive = executive
        self.watch_path = watch_path.resolve()
        self.debounce_ms = debounce_ms
        self.batch_size = batch_size
        self.output = OutputContext.get_global()

        # Event tracking
        self.pending_events: Dict[Path, dict] = {}  # path -> {'action': str, 'timestamp': float}
        self.processing_paths: Set[Path] = set()  # Currently being processed

        # Watchdog setup
        self.observer = Observer()
        self.event_handler = IconicsEventHandler(self)

        # Control flags
        self._stop_event = ThreadEvent()
        self._processor_thread: Optional[Thread] = None

        logger.info(f"IconicsWatcher initialized: {self.watch_path} (debounce={debounce_ms}ms)")

    def register_event(self, path: Path, action: str):
        """
        Register a file event for debounced processing.

        Args:
            path: File path
            action: Event action ('created' or 'modified')
        """
        # Skip if already processing
        if path in self.processing_paths:
            logger.debug(f"Skipping {path.name} (already processing)")
            return

        # Update or add to pending events with current timestamp
        self.pending_events[path] = {
            'action': action,
            'timestamp': time.time()
        }

        if self.output and self.output.mode == 'table':  # verbose mode
            self.output.debug(f"Registered: {path.name} ({action})")

    def get_settled_events(self) -> list[FileEvent]:
        """
        Get events that have "settled" (no updates for debounce_ms).

        Returns:
            List of FileEvent objects ready for processing
        """
        now = time.time()
        debounce_seconds = self.debounce_ms / 1000.0
        settled = []

        # Find paths that haven't been updated recently
        paths_to_process = []
        for path, event_data in list(self.pending_events.items()):
            time_since_last_update = now - event_data['timestamp']

            if time_since_last_update >= debounce_seconds:
                paths_to_process.append(path)

        # Remove from pending and create FileEvent objects
        for path in paths_to_process:
            event_data = self.pending_events.pop(path)

            # Mark as processing
            self.processing_paths.add(path)

            # Create FileEvent (ready for future eBPF fields)
            settled.append(FileEvent(
                path=path,
                action=event_data['action'],
                timestamp=event_data['timestamp']
                # Future eBPF fields:
                # origin_process=None,
                # user=None
            ))

        return settled

    def process_settled_events(self):
        """
        Process events that have settled.

        Runs in background thread, continuously checking for settled events.
        """
        logger.info("Event processor started")

        while not self._stop_event.is_set():
            # Check for settled events
            settled = self.get_settled_events()

            if settled:
                # Batch processing (limit to batch_size to prevent GPU overload)
                batch = settled[:self.batch_size]

                if self.output and self.output.mode != 'quiet':
                    self.output.info(f"Processing {len(batch)} settled event(s)")

                for event in batch:
                    try:
                        # Hand off to Executive for ingestion
                        result = self.executive.handle_event(event)

                        if result and result.status != 'error':
                            if self.output and self.output.mode != 'quiet':
                                self.output.success(
                                    f"{event.path.name} → {result.icon_id} "
                                    f"({result.status}, conf={result.confidence:.3f})"
                                )

                            # Display audit corrections if any
                            if result.audit_corrections:
                                for correction in result.audit_corrections:
                                    if self.output:
                                        self.output.format_audit_correction(
                                            original_label=correction['from'],
                                            corrected_label=correction['to'],
                                            reason=correction['reason']
                                        )
                        else:
                            if self.output and self.output.mode != 'quiet':
                                error_msg = result.metadata.get('error', 'Unknown') if result else 'No result'
                                self.output.error(f"{event.path.name}: {error_msg}")

                    except Exception as e:
                        logger.error(f"Failed to process {event.path}: {e}")
                        if self.output and self.output.mode != 'quiet':
                            self.output.error(f"{event.path.name}: {str(e)}")

                    finally:
                        # Remove from processing set
                        self.processing_paths.discard(event.path)

            # Sleep briefly to prevent busy-waiting
            time.sleep(0.1)

        logger.info("Event processor stopped")

    def start(self):
        """
        Start watching the directory.

        Launches:
        1. Watchdog observer (file system monitoring)
        2. Event processor thread (debouncing and ingestion)
        """
        # Verify watch path exists
        if not self.watch_path.exists():
            self.watch_path.mkdir(parents=True, exist_ok=True)
            if self.output:
                self.output.info(f"Created watch directory: {self.watch_path}")

        # Start watchdog observer
        self.observer.schedule(
            self.event_handler,
            str(self.watch_path),
            recursive=False
        )
        self.observer.start()

        # Start event processor thread
        self._processor_thread = Thread(
            target=self.process_settled_events,
            daemon=True,
            name="IconicsEventProcessor"
        )
        self._processor_thread.start()

        if self.output:
            self.output.success(
                f"Watching: {self.watch_path} "
                f"(debounce={self.debounce_ms}ms, batch={self.batch_size})"
            )

        logger.info("IconicsWatcher started")

    def stop(self):
        """Stop watching and clean up resources."""
        if self.output and self.output.mode != 'quiet':
            self.output.info("Stopping watcher...")

        # Signal processor thread to stop
        self._stop_event.set()

        # Stop watchdog observer
        self.observer.stop()
        self.observer.join(timeout=5)

        # Wait for processor thread
        if self._processor_thread and self._processor_thread.is_alive():
            self._processor_thread.join(timeout=5)

        if self.output:
            self.output.success("Watcher stopped")

        logger.info("IconicsWatcher stopped")

    def get_stats(self) -> Dict:
        """Get watcher statistics."""
        return {
            'watch_path': str(self.watch_path),
            'debounce_ms': self.debounce_ms,
            'batch_size': self.batch_size,
            'pending_events': len(self.pending_events),
            'processing': len(self.processing_paths),
            'is_running': self.observer.is_alive() if self.observer else False
        }
