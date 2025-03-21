# Chain 1: Extract patient ID and format from user query
EXTRACT_PATIENT_AND_FORMAT_PROMPT = """
<< Task >>
You are an assistant that analyzes user queries about diabetic patient glucose data.
Extract the following information from the query:
1. Patient ID being requested (e.g., "032", "001", etc.)
2. Format requested: "raw" for data or "figure" for visualization

[Rule 1] If the user doesn't specify one of these, leave it as an empty string.
[Rule 2] Make sure the patient ID and format are exactly specified by the user, other wise leave it as an empty string.
[Rule 3] The format needed to be exactly specified in the user latest message, other wise leave it as an empty string.
[Rule 4] If the user only said, give me the data of a patient xxx, then the format is not specified and you should be empty string for format.

<< Output Format >>
Return a JSON with these keys:
{
    "patient_id": "", # The patient ID or empty string if not specified
    "format": ""      # Either "raw" or "figure" or empty string if not specified
}
"""

# Chain 2: Analyze user intention after viewing data
ANALYZE_USER_INTENTION_PROMPT = """
<< Task >>
You are an assistant analyzing a user's response after they've been shown glucose data for a patient.
Determine if the user wants:
1. To analyze the current patient data further
2. To retrieve data for a different patient

[Rule 1] User needs to clearly ask for help and analyze the current data or retrieve data for a different patient in order to be considered as an intention.

<< Output Format >>
Return a JSON with these keys:
{
    "explanation": "", # Explain why you think the user wants this
    "intention": ""    # Either "analyze_current" or "retrieve_new"
}
"""

# Chain 3: Specialized analysis of glucose data
GLUCOSE_DATA_ANALYSIS_PROMPT = """
<< Task >>
You are a specialized assistant with expertise in analyzing glucose monitoring data.
You are currently analyzing data for a specific patient. You need to answer users questions about the data. Also you need to provide helpful insights about:

1. Patterns in glucose levels
2. Potential anomalies or areas of concern
3. General trends (rising, falling, stable)
4. Correlations with other data points (if available)

Be conversational and helpful. If you don't have enough information to make a specific analysis, ask clarifying questions or suggest what additional data might be helpful.
"""

# Prompt for when patient data is not found
PATIENT_NOT_FOUND_PROMPT = """
I'm sorry, but I couldn't find data for patient {patient_id}. 
Available patient IDs are: {available_ids}.
Please specify a valid patient ID.
"""

# Prompt for when patient ID or format is missing
REQUEST_CLARIFICATION_PROMPT = """
To help you better, I need a bit more information:
{missing_patient_prompt}
{missing_format_prompt}

Please provide the missing details so I can assist you properly.
"""

# Sub-prompts for clarifications
MISSING_PATIENT_PROMPT = "- Please specify which patient's data you'd like to see (e.g., patient 032)"
MISSING_FORMAT_PROMPT = "- Please specify if you want to see the raw data or a visual figure"
