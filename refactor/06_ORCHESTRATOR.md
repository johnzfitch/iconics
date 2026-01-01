# ORCHESTRATOR IMPLEMENTATION

```python
from pathlib import Path
from dataclasses import dataclass
from typing import Literal, Callable
import json

class IconicsOrchestrator:
    """
    Coordinates multi-agent execution of the iconics vector subspace build.
    """
    
    def __init__(self, workspace_path: str, config: dict):
        self.workspace = Path(workspace_path)
        self.config = config
        self.phase_outputs: dict[int, PhaseOutput] = {}
        self.message_log: list[AgentMessage] = []
        self.current_agent: str = None
        self.current_phase: int = None
        
    def run(self, start_phase: int = 0, end_phase: int = 8):
        """Execute phases in sequence with validation gates."""
        
        for phase in range(start_phase, end_phase + 1):
            print(f"\n{'='*60}")
            print(f"PHASE {phase}: {self.phase_name(phase)}")
            print(f"{'='*60}\n")
            
            # Prepare context for agent
            context = self.build_phase_context(phase)
            
            # Invoke appropriate agent
            agent = self.get_agent_for_phase(phase)
            self.current_agent = agent
            self.current_phase = phase
            
            output = self.invoke_agent(agent, phase, context)
            
            # Validate output
            gate = self.get_validation_gate(phase)
            passed, failures = self.validate(output, gate)
            
            if not passed:
                if gate.auto_retry_on_fail:
                    output = self.retry_with_feedback(agent, phase, context, failures)
                else:
                    raise PhaseFailure(phase, failures)
            
            # Store output and prepare handoff
            self.phase_outputs[phase] = output
            self.log_handoff(phase, phase + 1)
            
        return self.generate_final_report()
    
    def phase_name(self, phase: int) -> str:
        """Return human-readable phase name."""
        names = {
            0: "Architecture Review",
            1: "Embedding Generation",
            2: "Subspace Analysis",
            3: "Retrieval Engine",
            4: "Evaluation Framework",
            5: "CLI Integration",
            6: "Cross-Validation",
            7: "LLM Integration",
            8: "Final Validation"
        }
        return names.get(phase, f"Phase {phase}")
    
    def get_agent_for_phase(self, phase: int) -> str:
        """Return the agent responsible for a phase."""
        mapping = {
            0: "architect",
            1: "embedding_engineer",
            2: "linear_algebra_specialist",
            3: "retrieval_engineer",
            4: "evaluation_specialist",
            5: "integration_engineer",
            6: "architect",
            7: "llm_integration_engineer",
            8: "architect"
        }
        return mapping.get(phase)
    
    def build_phase_context(self, phase: int) -> dict:
        """Assemble all context needed for a phase."""
        context = {
            "system_prompt": self.load_system_prompt(),
            "phase": phase,
            "workspace": str(self.workspace),
            "existing_files": self.list_workspace_files(),
            "prior_outputs": {p: self.phase_outputs[p] for p in range(phase)},
            "icon_catalog": self.load_icon_catalog(),
            "agent_responses": [],
        }
        
        # Phase-specific additions
        if phase >= 1:
            context["architecture_decision"] = self.load_file("architecture_decision.md")
        if phase >= 2:
            context["embeddings_metadata"] = self.load_json("embeddings/metadata.json")
        if phase >= 3:
            context["subspace_analysis"] = self.load_json("subspace/component_analysis.json")
        if phase >= 7:
            # LLM integration needs semantic mapping for SKILL.md generation
            context["semantic_mapping"] = self.load_json("subspace/semantic_mapping.json")
            context["cli_commands"] = self.get_cli_commands()
            
        return context
    
    def invoke_agent(self, agent: str, phase: int, context: dict) -> PhaseOutput:
        """
        Invoke an Opus agent with full context.
        Returns structured output.
        """
        prompt = self.build_agent_prompt(agent, phase, context)
        
        # Agent execution loop - agent works until phase complete
        agent_complete = False
        iteration = 0
        max_iterations = 20
        
        while not agent_complete and iteration < max_iterations:
            response = self.call_opus(prompt, agent_context=context)
            
            # Parse agent actions
            actions = self.parse_agent_actions(response)
            
            for action in actions:
                if action.type == "create_file":
                    self.write_file(action.path, action.content)
                elif action.type == "run_command":
                    result = self.execute_command(action.command)
                    context["last_command_result"] = result
                elif action.type == "request_review":
                    # Pause for human or architect review
                    self.request_review(action.reviewer, action.artifact)
                elif action.type == "phase_complete":
                    agent_complete = True
                    break
                elif action.type == "query_agent":
                    # Cross-agent communication
                    response = self.route_query(action.target_agent, action.query)
                    context["agent_responses"].append(response)
            
            iteration += 1
            prompt = self.build_continuation_prompt(context, response)
        
        return self.extract_phase_output(context)
    
    def retry_with_feedback(
        self, 
        agent: str, 
        phase: int, 
        context: dict, 
        failures: list[str]
    ) -> PhaseOutput:
        """Re-invoke agent with specific failure feedback."""
        
        context["retry_attempt"] = context.get("retry_attempt", 0) + 1
        context["validation_failures"] = failures
        context["remediation_required"] = True
        
        feedback_prompt = f"""
        VALIDATION FAILED - REMEDIATION REQUIRED
        
        The following checks failed:
        {chr(10).join(f'- {f}' for f in failures)}
        
        Please fix these issues and re-output the affected files.
        Do not restart from scratch - modify only what's needed.
        """
        
        context["feedback"] = feedback_prompt
        return self.invoke_agent(agent, phase, context)

    def route_query(self, target_agent: str, query: str) -> str:
        """Handle cross-agent queries during execution."""
        
        msg = AgentMessage(
            from_agent=self.current_agent,
            to_agent=target_agent,
            phase=self.current_phase,
            message_type="query",
            payload={"query": query},
            requires_response=True,
            priority="blocking"
        )
        self.message_log.append(msg)
        
        # Invoke target agent with query context
        response = self.call_opus(
            prompt=f"Query from {msg.from_agent}: {query}",
            agent_context={"role": target_agent, "query_mode": True}
        )
        
        return response
    
    def validate(self, output: PhaseOutput, gate: ValidationGate) -> tuple[bool, list[str]]:
        """Run validation checks and return (passed, failures)."""
        failures = []
        
        for i, check in enumerate(gate.checks):
            try:
                if not check(self.build_validation_context(output)):
                    failures.append(f"Check {i+1} failed")
            except Exception as e:
                failures.append(f"Check {i+1} raised exception: {e}")
        
        # Check required approvals
        for approver in gate.required_approvals:
            if approver == "human":
                if not self.get_human_approval(output):
                    failures.append("Human approval not granted")
            else:
                if not self.get_agent_approval(approver, output):
                    failures.append(f"{approver} approval not granted")
        
        return len(failures) == 0, failures
    
    def log_handoff(self, from_phase: int, to_phase: int):
        """Log phase transition."""
        print(f"\n[HANDOFF] Phase {from_phase} → Phase {to_phase}")
        print(f"  Status: {self.phase_outputs[from_phase].status}")
        print(f"  Files created: {len(self.phase_outputs[from_phase].files_created)}")
        if self.phase_outputs[from_phase].notes_for_next_phase:
            print(f"  Notes: {self.phase_outputs[from_phase].notes_for_next_phase}")
    
    def generate_final_report(self) -> dict:
        """Generate summary report of full orchestration run."""
        return {
            "phases_completed": len(self.phase_outputs),
            "total_time_seconds": sum(p.time_taken_seconds for p in self.phase_outputs.values()),
            "files_created": [f for p in self.phase_outputs.values() for f in p.files_created],
            "issues_encountered": [i for p in self.phase_outputs.values() for i in p.issues],
            "message_count": len(self.message_log),
            "success": all(p.status == "success" for p in self.phase_outputs.values()),
            "llm_integration": {
                "skill_file": "skill/SKILL.md",
                "new_commands": ["batch-query", "provision", "scan-emoji", "convert-emoji", "generate-imports"],
                "emoji_types_mapped": self.phase_outputs.get(7, {}).metrics.get("emoji_types_mapped", 0)
            }
        }
    
    def get_cli_commands(self) -> list[str]:
        """Get list of available CLI commands for LLM integration phase."""
        return [
            "embed", "analyze-subspace", "query", "traverse", "interpolate",
            "eval-retrieval", "compare-methods", "subspace-info", "list-axes",
            "residual", "find-gaps", "export-embeddings", "rebuild-index"
        ]
    
    # Stub methods to be implemented
    def load_system_prompt(self) -> str: pass
    def list_workspace_files(self) -> list[str]: pass
    def load_icon_catalog(self) -> dict: pass
    def load_file(self, path: str) -> str: pass
    def load_json(self, path: str) -> dict: pass
    def build_agent_prompt(self, agent: str, phase: int, context: dict) -> str: pass
    def call_opus(self, prompt: str, agent_context: dict) -> str: pass
    def parse_agent_actions(self, response: str) -> list: pass
    def write_file(self, path: str, content: str): pass
    def execute_command(self, command: str) -> str: pass
    def request_review(self, reviewer: str, artifact: str): pass
    def build_continuation_prompt(self, context: dict, response: str) -> str: pass
    def extract_phase_output(self, context: dict) -> PhaseOutput: pass
    def build_validation_context(self, output: PhaseOutput) -> dict: pass
    def get_human_approval(self, output: PhaseOutput) -> bool: pass
    def get_agent_approval(self, agent: str, output: PhaseOutput) -> bool: pass
    def get_validation_gate(self, phase: int) -> ValidationGate: pass


class PhaseFailure(Exception):
    """Raised when a phase fails validation and cannot be retried."""
    def __init__(self, phase: int, failures: list[str]):
        self.phase = phase
        self.failures = failures
        super().__init__(f"Phase {phase} failed: {failures}")
```

---

## LLM Integration Phase Details

The LLM integration phase (Phase 7) has specific requirements:

```python
def build_phase7_context(self, base_context: dict) -> dict:
    """
    Build context specifically for LLM integration phase.
    """
    context = base_context.copy()
    
    # Load semantic mapping for axis names
    semantic_mapping = self.load_json("subspace/semantic_mapping.json")
    context["semantic_axes"] = [
        {
            "name": axis_name,
            "pc_index": data["pc_index"],
            "correlation": data["correlation"],
            "negative_pole": data.get("negative_exemplars", [])[:3],
            "positive_pole": data.get("positive_exemplars", [])[:3]
        }
        for axis_name, data in semantic_mapping.items()
        if data.get("p_value", 1.0) < 0.01
    ]
    
    # Emoji mapping for scanner
    context["emoji_map"] = EmojiScanner.EMOJI_MAP
    
    # Available CLI commands for SKILL.md
    context["cli_commands"] = self.get_cli_commands()
    
    # Framework templates for generate-imports
    context["import_templates"] = {
        "react": "import {name} from '{path}';",
        "vue": "import {name} from '{path}';",
        "css": ".icon-{name} {{ background-image: url('{path}'); }}",
        "typescript": "export const {name}: string = '{path}';"
    }
    
    return context
```
