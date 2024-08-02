# Einscan-MRI-Alignment
Aligns 3D einscan meshes to those produced from MRI scans to enable the functional information from an OPM-MEG experiment to be overlaid onto structural brain imagery obtained via MRI.

This tool was produced as part of my internship at the UoN OPM-MEG research group, with the aim of seeking to automate a time consuming aspect of their data processing. It takes an initial input of the two preauricular points as well as the underside of the nasal tip and uses this information to transform both meshes into a common coordinate space. The program then attempts to identify common landmarks on both meshes which it then uses to achieve as close of an alignment as possible. 

The program outputs the two aligned meshes as well as the transformation matrices used to achieve the alignment. It should be noted that the program has only been tested on caucasian, male faces and therefore the bounds used in each step of the search process may have to be adjusted for wider use.

The meshes included in this repository were uploaded with the subjects' permission. 

## Usage
Note: The program has only been verified to run correctly on Windows

### Python Version
Python 3.10.9 was used for development and testing and is recommended for running the program. If using `pyenv`, the following commands can be used:
1. `pyenv install 3.10.9`
2. `pyenv local 3.10.9`

### Setting up the Python Environment
1. Create your env folder: `python -m venv env`

2. Install the required dependencies: `pip install -r requirements.txt`

### Running the Program
1. Activate the Environment: `.\env\Scripts\activate`

2. Run the main script: `python .\head_to_mri.py`
