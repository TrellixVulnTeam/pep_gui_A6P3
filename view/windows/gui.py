import os

import PySimpleGUI as sg

from config import PipelineManifest
from config.exceptions import MissingPortsException
from core.job import create_job
from datasets import DatasetManifest
from fonts import Fonts
from windows.initial_setup import initial_setup
from windows.job_runner import run_job
from layouts import DatasetSelectionLayout, PipelineSelectionLayout, LayoutSection
from view.settings import get_settings, SettingsNames, WINDOW_ICON

sg.theme('SystemDefaultForReal')
initial_setup()
gui_settings = get_settings()

pm = PipelineManifest()
dm = DatasetManifest(manifest_filepath=gui_settings[SettingsNames.dataset_manifest_filepath])

dataset_tab = DatasetSelectionLayout(dm)
pipeline_tab = PipelineSelectionLayout(pm)


# ======== Layout helpers =========
def create_frame(tl: LayoutSection):
    return sg.Frame(layout=tl.get_layout(), title=tl.layout_name, font=Fonts.title_medium, title_color='#0b64c5')

def popup_ok(msg):
    max_line_width = 200
    current = sg.MESSAGE_BOX_LINE_WIDTH
    for line in msg.split('\n'):
        if len(line) > current:
            current = len(line)
    sg.popup_ok(msg, location=gui_settings[SettingsNames.window_location], line_width=min(max_line_width, current))


# ======== Create the Layout =========
layout = [
    [sg.Text('Polar Ecosystems Program Batch Runner', size=(38, 1), justification='center', font=Fonts.title_large,
             relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-', enable_events=True, text_color='#063970')]]

layout += [[create_frame(dataset_tab)],
           [create_frame(pipeline_tab)]]

# Jobs base directory and job name inputs
desktop_dir = os.path.expanduser("~/Desktop/")  # default
layout += [
    [
        sg.Text('Jobs Base Directory', font=Fonts.description),
        sg.Input(gui_settings.get(SettingsNames.job_directory, desktop_dir), key='-job_dir-IN-', size=(50, 1)),
        sg.FolderBrowse(initial_folder=desktop_dir)
    ],
    [
        sg.Text('Job Name', font=Fonts.description),
        sg.Input('', key='-job_name-IN-', size=(20, 1))
    ]
]
layout += [[sg.Button('Create Job', key='-CREATE_JOB-')]]

location = (0, 0)
if SettingsNames.window_location in gui_settings.get_dict():
    location = gui_settings[SettingsNames.window_location]

# menu_def = [['&File', ['&Open     Ctrl-O', '&Save       Ctrl-S', '&Properties', 'E&xit']],
#             ['&Edit', [['Special', 'Normal', ['Normal1', 'Normal2']], 'Undo'], ],
#             ['!Disabled', [['Special', 'Normal', ['Normal1', 'Normal2']], 'Undo'], ],
#             ['&Toolbar', ['---', 'Command &1::Command_Key', 'Command &2', '---', 'Command &3', 'Command &4']],
#             ['&Help', ['&About...']], ]

# layout = [[[Menubar(menu_def, sg.theme_button_color()[1], sg.theme_button_color()[0], (5, 0))]]] + layout
# layout = [[sg.Menu(menu_def, tearoff=False, key='-MENU BAR-')]] + layout

window = sg.Window('PEP-TK: Job Configuration', layout,
                   default_element_size=(12, 1), location=location, icon=WINDOW_ICON, titlebar_icon=WINDOW_ICON)


# ======== Handler helper functions =========
def cache_settings(values):
    # set the job homedir in the app settings
    selected_job_directory = values['-job_dir-IN-']
    if os.path.isdir(selected_job_directory):
        gui_settings[SettingsNames.job_directory] = selected_job_directory


def validate_inputs(values) -> bool:
    selected_job_directory = values['-job_dir-IN-']
    selected_job_name = values['-job_name-IN-']
    job_dir = os.path.join(selected_job_directory, selected_job_name)
    datasets = dataset_tab.get_selected_datasets()
    pipeline = pipeline_tab.get_selected_pipeline()

    # Check if no datasets were selected
    if len(datasets) < 1:
        popup_ok('No datasets were selected.  Must select one or more datasets above.')
        return False

    # if pipeline_tab.selected_pipeline is None:
    if not pipeline_tab.validate(values):
        popup_ok('Either a pipeline isn\'t selected or error in configuration values.')
        return False

    # Check for missing ports(aka if datasets/pipeline are not compatible)
    missing_ports = {}
    for dataset in datasets:
        try:
            pipeline.get_pipeline_dataset_environment(dataset)
        except MissingPortsException as e:
            missing_ports[e.dataset_name] = e.ports
    if len(missing_ports) > 0:
        msg = "Datasets aren't compatible with the selected pipeline: \n"
        for dataset_name, ports in missing_ports.items():
            msg += "%s: MISSING(%s)\n" % (dataset_name, ', '.join(ports))
        popup_ok(msg)
        return False

    # Check if the job base directory doesn't exist
    if not os.path.isdir(selected_job_directory):
        popup_ok(f'Jobs base directory {selected_job_directory} does not exist.')
        return False

    # Check if the selected name is an empty string
    if selected_job_name == '':
        popup_ok('No job name entered')
        return False

    # Check if the job directory(within the base directory) already exists
    if os.path.isdir(job_dir):
        popup_ok(f'Job {selected_job_name} already exists, cannot override an existing job.\n{job_dir}')
        return False



    return True

# ======== Window / Event loop =========
CREATED_JOB_PATH = None
while True:
    event, values = window.read()
    # sg.popup_non_blocking(event, values)
    print(event, values)
    try:
        gui_settings[SettingsNames.window_location] = window.CurrentLocation()
    except:
        pass
    if event == sg.WIN_CLOSED:  # always,  always give a way out!
        break
    if event == '-CREATE_JOB-':
        cache_settings(values)
        if not validate_inputs(values):
            continue

        selected_job_directory = values['-job_dir-IN-']
        selected_job_name = values['-job_name-IN-']

        pipeline = pipeline_tab.get_selected_pipeline()
        datasets = dataset_tab.get_selected_datasets()
        try:
            job_dir = os.path.join(selected_job_directory, selected_job_name)
            CREATED_JOB_PATH = create_job(pipeline=pipeline, datasets=datasets, directory=job_dir)
        except Exception as e:
            popup_ok(f'There was an error creating the job: \n {str(e)}.\n I would recommend sending this error to Yuval.')
            continue

        break # END: close window

    dataset_tab.handle(window, event, values)
    pipeline_tab.handle(window, event, values)
window.close()

if CREATED_JOB_PATH:  # END: start running job
    run_job(CREATED_JOB_PATH)