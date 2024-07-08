import pandas as pd
import numpy as np
import random
import os
import json

patients_to_exclude = []

new_directory = r"../data/patients/"
os.chdir(new_directory)

list_dir = os.listdir()

for file in list_dir:
    with open(file, 'r') as f:
        read_t_file = json.load(f)

    some_patients = read_t_file.keys()

    patients_to_exclude.extend(some_patients)

patients_to_exclude = set(patients_to_exclude)
patients_to_exclude = list(patients_to_exclude)

print()
print("To avoid reusing patients, below are the patients to exclude:")
print(patients_to_exclude)
print()