import os
import asyncio
from enum import Enum, auto
import pandas as pd
from openai import AsyncOpenAI
from config import API_KEY
from utilities import openai_async_wrapper
from data_utils import get_available_patient_ids, get_patient_data, format_raw_data, generate_glucose_plot, display_raw_data_popup, generate_conversation_pdf
from prompts import *

class BotState(Enum):
    """Simple enumeration of possible bot states"""
    INITIAL = auto()              # No patient selected yet
    NEEDS_CLARIFICATION = auto()  # Missing information
    DATA_RETRIEVED = auto()       # Successfully retrieved patient data 
    ANALYZING_DATA = auto()       # Analyzing current patient data

class GlucoseDataBot:
    """Main bot class with integrated conversation tracking and state management"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=API_KEY)
        self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CGMacros")
        self.patient_ids = get_available_patient_ids(self.data_path)
        
        # State management
        self.state = BotState.INITIAL
        self.context = {}  # Stores state-related information
        
        # Conversation history
        self.conversation_history = []
        self.max_history_length = 6  # Keep last 3 exchanges
    
    def update_history(self, role, content):
        """Add a message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def get_conversation_context(self):
        """Format conversation history for the LLM"""
        if not self.conversation_history:
            return ""
        
        formatted = "\n\nRecent conversation:\n"
        for msg in self.conversation_history:
            role = "User" if msg["role"] == "user" else "Bot"
            formatted += f"{role}: {msg['content']}\n"
        return formatted
    
    async def process_message(self, user_message):
        """Main entry point for processing user messages"""
        # Always update history with user message
        self.update_history("user", user_message)
        
        # Process message based on current state
        if self.state == BotState.INITIAL:
            response = await self._handle_initial_message(user_message)
        elif self.state == BotState.NEEDS_CLARIFICATION:
            response = await self._handle_clarification(user_message)
        elif self.state == BotState.DATA_RETRIEVED:
            response = await self._handle_data_retrieved(user_message)
        elif self.state == BotState.ANALYZING_DATA:
            response = await self._handle_analysis(user_message)
        else:
            # Fallback to initial state if unknown
            self.state = BotState.INITIAL
            response = await self._handle_initial_message(user_message)
        
        # Update history with bot response
        self.update_history("bot", response)
        return response
    
    async def _handle_initial_message(self, message):
        """Handle messages in the INITIAL state"""
        # Check if user wants to export conversation as PDF
        if any(keyword in message.lower() for keyword in ["pdf", "export", "save conversation", "export conversation"]):
            patient_id = self.context.get("patient_id")
            return self.export_conversation_as_pdf(patient_id)
            
        # Extract patient ID and format
        query_info = await self._extract_patient_and_format(message)
        
        # Check if we have partial information from previous messages
        patient_id = query_info.get("patient_id") or self.context.get("partial_patient_id")
        format_type = query_info.get("format") or self.context.get("partial_format")
        
        # Save any partial information
        if patient_id:
            self.context["partial_patient_id"] = patient_id
        if format_type:
            self.context["partial_format"] = format_type
            
        # Check what information is missing
        missing = []
        if not patient_id:
            missing.append("patient_id")
        if not format_type:
            missing.append("format")
            
        if missing:
            # Need clarification
            self.context["missing_info"] = missing
            self.state = BotState.NEEDS_CLARIFICATION
            return self._create_clarification_message(missing)
        
        # Check if patient exists
        if patient_id not in self.patient_ids:
            return self._create_patient_not_found_message(patient_id)
            
        # We have all the information we need and the patient exists
        # Get the data and return it
        patient_data = get_patient_data(self.data_path, patient_id)
        
        # Clear partial info since we have complete data now
        if "partial_patient_id" in self.context:
            del self.context["partial_patient_id"]
        if "partial_format" in self.context:
            del self.context["partial_format"]
            
        # Store the current data in context
        self.context["patient_id"] = patient_id 
        self.context["format"] = format_type
        self.context["patient_data"] = patient_data
        self.state = BotState.DATA_RETRIEVED
        
        # Return the data in the requested format
        if format_type == "figure":
            result = generate_glucose_plot(patient_data, patient_id)
        else:  # raw data format
            # Use the new popup function instead of just returning formatted text
            result = display_raw_data_popup(patient_data, patient_id)
            
        # Add offer for further assistance
        result += "\n\nI can help you analyze this data further, or I can retrieve data for another patient. What would you like to do?"
        return result
    
    async def _handle_clarification(self, message):
        """Handle messages when we need clarification"""
        # Check if user wants to export conversation as PDF
        if any(keyword in message.lower() for keyword in ["pdf", "export", "save conversation", "export conversation"]):
            patient_id = self.context.get("patient_id")
            return self.export_conversation_as_pdf(patient_id)
            
        # Extract info from the new message
        query_info = await self._extract_patient_and_format(message)
        
        # Get what was previously missing
        missing = self.context.get("missing_info", [])
        
        # Combine with any partial information we already have
        patient_id = query_info.get("patient_id") or self.context.get("partial_patient_id")
        format_type = query_info.get("format") or self.context.get("partial_format")
        
        # Save the new information
        if patient_id:
            self.context["partial_patient_id"] = patient_id
        if format_type:
            self.context["partial_format"] = format_type
            
        # Check what's still missing
        still_missing = []
        if "patient_id" in missing and not patient_id:
            still_missing.append("patient_id")
        if "format" in missing and not format_type:
            still_missing.append("format")
            
        if still_missing:
            # We still need more information
            self.context["missing_info"] = still_missing
            return self._create_clarification_message(still_missing)
            
        # We now have all the information - go back to initial state with a complete query
        self.state = BotState.INITIAL
        complete_query = f"Get {format_type} data for patient {patient_id}"
        return await self._handle_initial_message(complete_query)
    
    async def _handle_data_retrieved(self, message):
        """Handle messages after data has been retrieved"""
        # Check if user wants to export conversation as PDF
        if any(keyword in message.lower() for keyword in ["pdf", "export", "save conversation", "export conversation"]):
            patient_id = self.context.get("patient_id")
            return self.export_conversation_as_pdf(patient_id)
        
        # Analyze what the user wants to do next
        intention = await self._analyze_intention(message)
        
        if intention["intention"] == "analyze_current":
            # User wants to analyze the current data
            self.state = BotState.ANALYZING_DATA
            return await self._handle_analysis(message)
        elif intention["intention"] == "retrieve_new":
            # User wants data for a different patient
            self.state = BotState.INITIAL 
            # Clear current patient data but save any new patient info in the message
            patient_id = self.context.get("patient_id")
            self.context.clear()
            
            # Check if the new message contains patient info
            query_info = await self._extract_patient_and_format(message)
            if query_info.get("patient_id"):
                self.context["partial_patient_id"] = query_info.get("patient_id")
            if query_info.get("format"):
                self.context["partial_format"] = query_info.get("format")
                
            # Process as a new initial query
            return await self._handle_initial_message(message)
        else:
            # Unclear intention
            return "I'm not sure what you'd like to do. Would you like to analyze this patient's data further, or retrieve data for a different patient?"
    
    async def _handle_analysis(self, message):
        """Handle analysis of patient data"""
        # Check if user wants to export conversation as PDF
        if any(keyword in message.lower() for keyword in ["pdf", "export", "save conversation", "export conversation"]):
            patient_id = self.context.get("patient_id")
            return self.export_conversation_as_pdf(patient_id)
            
        # Make sure we have data to analyze
        patient_data = self.context.get("patient_data")
        patient_id = self.context.get("patient_id")
        
        if patient_data is None or patient_data.empty or not patient_id:
            self.state = BotState.INITIAL
            return "I don't have any patient data to analyze. Please specify which patient's data you'd like to see."
            
        # Analyze the data based on the user's query
        analysis = await self._analyze_glucose_data(message, patient_id, patient_data)
        self.state = BotState.DATA_RETRIEVED
        return analysis
    
    async def _extract_patient_and_format(self, message):
        """Extract patient ID and format from user message"""
        context = self.get_conversation_context()
        full_prompt = f"{context}\nCurrent query: {message}"
        
        result = await openai_async_wrapper(
            model_name="gpt-4o",
            sys_prompt=EXTRACT_PATIENT_AND_FORMAT_PROMPT,
            user_prompt=full_prompt,
            output="json",
            user_client=self.client
        )
        
        return result
    
    async def _analyze_intention(self, message):
        """Determine if user wants to analyze current data or get new data"""
        patient_id = self.context.get("patient_id")
        context = f"The user has just viewed glucose data for patient {patient_id}."
        recent_conversation = self.get_conversation_context()
        full_prompt = f"User message: {message}"
        
        result = await openai_async_wrapper(
            model_name="gpt-4o",
            sys_prompt=ANALYZE_USER_INTENTION_PROMPT,
            user_prompt=full_prompt,
            output="json",
            user_client=self.client
        )
        
        return result
    
    async def _analyze_glucose_data(self, message, patient_id=None, patient_data=None):
        """Analyze glucose data for insights"""
        # Use provided data or get from context
        if patient_id is None:
            patient_id = self.context.get("patient_id")
        if patient_data is None:
            patient_data = self.context.get("patient_data")
            
        # Prepare data summary
        stats = {
            "min_glucose": patient_data["Dexcom GL"].min(),
            "max_glucose": patient_data["Dexcom GL"].max(),
            "avg_glucose": patient_data["Dexcom GL"].mean(),
            "std_glucose": patient_data["Dexcom GL"].std(),
            "data_points": len(patient_data),
            "time_range": f"From {patient_data['Timestamp'].iloc[0]} to {patient_data['Timestamp'].iloc[-1]}"
        }
        
        summary = f"""
        Time Range: {stats['time_range']}
        Number of readings: {stats['data_points']}
        Minimum glucose: {stats['min_glucose']:.2f}
        Maximum glucose: {stats['max_glucose']:.2f}
        Average glucose: {stats['avg_glucose']:.2f}
        Standard deviation: {stats['std_glucose']:.2f}
        """
        
        # Get analysis from LLM
        conversation_context = self.get_conversation_context()
        full_prompt = f"Data for patient {patient_id}:\n{summary}\n{conversation_context}\nCurrent query: {message}"
        
        analysis = await openai_async_wrapper(
            model_name="gpt-4o",
            sys_prompt=GLUCOSE_DATA_ANALYSIS_PROMPT,
            user_prompt=full_prompt,
            output="text",
            user_client=self.client
        )
        return analysis
    
    def _create_clarification_message(self, missing_info):
        """Create a message asking for clarification"""
        missing_patient_prompt = MISSING_PATIENT_PROMPT if "patient_id" in missing_info else ""
        missing_format_prompt = MISSING_FORMAT_PROMPT if "format" in missing_info else ""
        
        return REQUEST_CLARIFICATION_PROMPT.format(
            missing_patient_prompt=missing_patient_prompt,
            missing_format_prompt=missing_format_prompt
        )
    
    def _create_patient_not_found_message(self, patient_id):
        """Create a message when patient is not found"""
        # Show only the first 10 patient IDs
        available_ids_sample = ", ".join(self.patient_ids[:10])
        response = PATIENT_NOT_FOUND_PROMPT.format(
            patient_id=patient_id,
            available_ids=available_ids_sample
        )
        
        # Add helpful instructions
        response += "\n\nPlease provide another patient ID from the list above. For example: 'Show me data for patient 015'"
        
        # Mention if there are more patients available
        if len(self.patient_ids) > 10:
            response += f"\n\nNote: I've shown only the first 10 patient IDs. There are {len(self.patient_ids)} patients available in total."
        
        return response
    
    def export_conversation_as_pdf(self, patient_id=None):
        """Export the conversation history as a PDF file"""
        return generate_conversation_pdf(self.conversation_history, patient_id)