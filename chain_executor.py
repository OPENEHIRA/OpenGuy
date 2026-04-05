"""
chain_executor.py - Execute multi-step command chains.
Parses "do X AND do Y AND do Z" and executes sequentially.
"""

import re
from typing import List, Dict, Any, Optional
from parser import parse


class CommandChain:
    """Parse and execute multi-step robot command chains."""
    
    def __init__(self):
        self.current_step = 0
        self.commands: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
    
    def parse_chain(self, text: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Parse a chain of commands separated by 'and', 'then', '&', or commas.
        Examples:
            "move forward AND grab"
            "move left, rotate right, release"
            "pick up the block THEN move forward THEN release"
        
        Returns list of parsed commands.
        """
        self.commands = []
        self.current_step = 0
        self.results = []
        
# Split by common delimiters while preserving original case
        separators = [r'\s+and\s+', r'\s+then\s+', r'\s*&\s*', r',']
        pattern = '|'.join(separators)
        command_texts = [cmd.strip() for cmd in re.split(pattern, text, flags=re.IGNORECASE) if cmd.strip()]
        
        if not command_texts:
            return []
        
        # If only one command, no chain needed
        if len(command_texts) == 1:
            parsed = parse(command_texts[0], api_key=api_key, use_ai=True)
            parsed['_chain_step'] = 0
            parsed['_chain_total'] = 1
            self.commands = [parsed]
            return self.commands
        
        # Parse each command in the chain
        for i, cmd_text in enumerate(command_texts):
            parsed = parse(cmd_text, api_key=api_key, use_ai=True)
            parsed['_chain_step'] = i
            parsed['_chain_total'] = len(command_texts)
            self.commands.append(parsed)
        
        return self.commands
    
    def get_next_command(self) -> Optional[Dict[str, Any]]:
        """Get the next command in the chain."""
        if self.current_step < len(self.commands):
            return self.commands[self.current_step]
        return None
    
    def advance(self, result: Dict[str, Any]) -> None:
        """Record result and move to next command."""
        self.results.append(result)
        self.current_step += 1
    
    def is_complete(self) -> bool:
        """Check if all commands in chain are executed."""
        return self.current_step >= len(self.commands)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get chain execution progress."""
        return {
            "current_step": self.current_step,
            "total_steps": len(self.commands),
            "percentage": (self.current_step / len(self.commands) * 100) if self.commands else 0,
            "is_complete": self.is_complete(),
            "commands": self.commands,
            "results": self.results,
        }
    
    def reset(self) -> None:
        """Reset chain executor."""
        self.commands = []
        self.results = []
        self.current_step = 0


# Global chain executor instance
_chain = CommandChain()


def parse_command_chain(text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Parse a command chain and return all commands."""
    commands = _chain.parse_chain(text, api_key=api_key)
    return {
        "is_chain": len(commands) > 1,
        "commands": commands,
        "total_steps": len(commands),
        "progress": _chain.get_progress(),
    }


def get_chain_command(step: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Get a specific command from the chain."""
    if step is not None:
        if 0 <= step < len(_chain.commands):
            return _chain.commands[step]
        return None
    return _chain.get_next_command()


def execute_chain_step(result: Dict[str, Any]) -> Dict[str, Any]:
    """Record result and get next command."""
    _chain.advance(result)
    next_cmd = _chain.get_next_command()
    return {
        "success": True,
        "step_completed": _chain.current_step - 1,
        "next_command": next_cmd,
        "progress": _chain.get_progress(),
    }


def get_chain_status() -> Dict[str, Any]:
    """Get current chain status."""
    return _chain.get_progress()


def reset_chain() -> None:
    """Reset the chain executor."""
    _chain.reset()
