from enum import Enum, auto

class BotState(Enum):
    """Enumeration of possible states for the glucose data bot."""
    INITIAL = auto()              # No patient selected yet
    CLARIFICATION_NEEDED = auto() # Missing information (patient ID or format)
    PATIENT_NOT_FOUND = auto()    # Invalid patient ID provided
    DATA_RETRIEVED = auto()       # Successfully retrieved patient data 
    ANALYZING_DATA = auto()       # User wants to analyze current patient data
    RETRIEVING_NEW = auto()       # User wants data for a different patient

class StateMachine:
    """Manages state transitions for the conversation flow."""
    
    def __init__(self, initial_state=BotState.INITIAL):
        self.current_state = initial_state
        self.context = {}  # Holds relevant information for the current state
    
    def transition_to(self, new_state, **context):
        """
        Transition to a new state and update context.
        
        Args:
            new_state: The state to transition to
            **context: Additional context data for the new state
        """
        previous_state = self.current_state
        self.current_state = new_state
        
        # Update context with new information
        self.context.update(context)
        
        # Clear specific context when transitioning to certain states
        if new_state == BotState.INITIAL:
            # When transitioning to INITIAL, preserve partial information
            # only if we're coming from CLARIFICATION_NEEDED or RETRIEVING_NEW
            if previous_state not in [BotState.CLARIFICATION_NEEDED, BotState.RETRIEVING_NEW]:
                # Clear patient-specific data when returning to initial state from other states
                keys_to_remove = [
                    'patient_id', 'format', 'patient_data', 
                    'partial_patient_id', 'partial_format'
                ]
                for key in keys_to_remove:
                    if key in self.context:
                        del self.context[key]
    
    def is_in_state(self, *states):
        """Check if current state is one of the provided states."""
        return self.current_state in states
    
    def get_context(self, key, default=None):
        """Get a value from the context dictionary."""
        return self.context.get(key, default)
    
    def set_context(self, key, value):
        """Set a value in the context dictionary."""
        self.context[key] = value
        
    def clear_partial_info(self):
        """Clear any partial information stored in the context."""
        keys_to_remove = ['partial_patient_id', 'partial_format', 'missing_info']
        for key in keys_to_remove:
            if key in self.context:
                del self.context[key] 