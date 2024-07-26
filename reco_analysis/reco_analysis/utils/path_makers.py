import reco_analysis.config as config
from typing import Literal

DEFAULT_TIMESTAMP = ''

def path_maker(config_params: dict):
    """
    Creates a path for saving or loading files based on the type of file and the model and prompt used.
    
    Args:
        config_params: Dictionary containing configuration parameters.
            - type (str): The type of file to create the path for. Can be one of 'transcripts', 'transcripts_eval', 'transcripts_eval_improvements', 'summaries', 'summaries_eval', 'summaries_eval_improvements'.
            - termination (str): The type of transcript to create the path for. Can be either 'full' or 'short'. 'Full' is the full chat transcript, while 'short' is the extracted chat transcript.
            - model_name (str): The name of the model used in the transcript. Can be one of '3.5', '4o-mini', '4o'.
            - patient_prompt (str): The type of patient prompt used in the transcript. Can be one of 'base', 'reluctant', 'distracted'.
            - doctor_prompt (str): The type of doctor prompt used in the transcript. Can be either 'base' or 'improved'.
            - timestamp (str, optional): The timestamp for the file. Defaults to a global TIMESTAMP variable if not provided in the config dictionary.
    Returns:
        str: A formatted string representing the path for the specified file configuration.
    """
    type = config_params['type']
    termination = config_params['termination']
    model_name = config_params['model_name']
    patient_prompt = config_params['patient_prompt']
    doctor_prompt = config_params['doctor_prompt']
    timestamp = config_params['doctor_prompt']
    
    # Set the folder path depending on type
    if type == 'transcripts':
        folder_path = config.TRANSCRIPTS_DIR
    elif type in ['transcripts_eval', 'transcripts_eval_improvements']:
        folder_path = config.TRANSCRIPTS_EVALUATION_DIR
    elif type == 'summaries':
        folder_path = config.SUMMARIES_DIR
    elif type in ['summaries_eval', 'summaries_eval_improvements']:
        folder_path = config.SUMMARIES_EVALUATION_DIR

    # Reformat fields
    model_name = 'gpt' + model_name.replace('4o-mini', '4o-m')
    patient_prompt = patient_prompt[:4] + 'pat'   
    doctor_prompt = doctor_prompt[:4] + 'doc'

    # Set to csv if this is an eval file
    if type in ['transcripts_eval', 'summaries_eval']:
        extension = 'csv'
    else:
        extension = 'json'

    if timestamp:
        return f"{folder_path}/{type}_{termination}_{model_name}_{patient_prompt}_{doctor_prompt}_{timestamp}.{extension}"
    else:
        return f"{folder_path}/{type}_{termination}_{model_name}_{patient_prompt}_{doctor_prompt}.{extension}"

def compile_paths(
        termination: Literal['full', 'short'],
        model_name: Literal['3.5', '4o-mini', '4o'],
        patient_prompt: Literal['base', 'reluctant', 'distracted'],
        doctor_prompt: Literal['base', 'improved'],
        timestamp = DEFAULT_TIMESTAMP
):
    """
    Compiles the paths for the chat transcripts, evaluation, and evaluation improvements based on the configuration parameters.

    Args:
        termination (str): The type of transcript to create the path for. Can be either 'full' or 'short'. 'Full' is the full chat transcript, while 'short' is the extracted chat transcript.
        model_name (str): The name of the model used in the transcript. Can be one of '3.5', '4o-mini', '4o'.
        patient_prompt (str): The type of patient prompt used in the transcript. Can be one of 'base', 'reluctant', 'distracted'.
        doctor_prompt (str): The type of doctor prompt used in the transcript. Can be either 'base' or 'improved'.
        timestamp (str, optional): The timestamp for the file. Defaults to a global TIMESTAMP

    Returns:
        Tuple[str, str, str]: A tuple containing the paths for the chat transcripts, evaluation, and evaluation improvements.
    """
    # Compile the dictionary
    config = {
        'termination': termination,
        'model_name': model_name,
        'patient_prompt': patient_prompt,
        'doctor_prompt': doctor_prompt,
        'timestamp': str(timestamp)
    }

    # Create the paths
    transcripts_path = path_maker({'type': 'transcripts', **config})
    transcripts_eval_path = path_maker({'type': 'transcripts_eval', **config})
    transcripts_eval_improvements_path = path_maker({'type': 'transcripts_eval_improvements', **config})

    # Return tuple
    return transcripts_path, transcripts_eval_path, transcripts_eval_improvements_path