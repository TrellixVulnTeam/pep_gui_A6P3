from typing import Dict

from config import PipelineManifest, ConfigOption, PipelineConfig
from fonts import Fonts
from tabs import TabLayout
import PySimpleGUI as sg
def pipeline_key(pipeline_name):
    return f'-F-{pipeline_name}-'

class PipelineConfigLayout(TabLayout):
    def __init__(self, pipeline_name, pipeline_manifest):
        self.pipeline_name = pipeline_name
        self.pipeline_manifest : PipelineManifest = pipeline_manifest
        self.selected_pipeline : PipelineConfig = self.pipeline_manifest[self.pipeline_name]
        self.event_keys = [self.reset_defaults_key, self.pipeline_frame_key]
        self.input_keys_to_config_name : Dict[str, str] = {}

    def get_layout(self):
        config_layout = []
        opts = self.selected_pipeline.parameters_group.options
        for o in opts:
            k = self.pipeline_config_input_key(o.name)
            self.event_keys.append(k)
            self.input_keys_to_config_name[k] = o.name
            row = [
                    sg.T(f'{o.name}:',font=Fonts.description_bold),
                    sg.I(key=k, default_text=o.value(),enable_events=True),
                    ]
            config_layout.append(row)
            config_layout.append([sg.T(o.description, font=Fonts.description, pad=((0, 0), (0, 0)))])
            config_layout.append([sg.Text('_'*100, pad=((0, 0), (0, 0)))])
        config_layout.append([sg.Button('Reset Defaults', key=self.reset_defaults_key)])
        return config_layout

    def handle(self, window, event, values):
        if event == self.reset_defaults_key:
            self.selected_pipeline.parameters_group.reset_all()
            for key, opt_name in self.input_keys_to_config_name.items():
                opt = self.selected_pipeline.parameters_group.get_config_option(opt_name)
                config_opt_value = opt.value()
                ui_value = values[key]
                window.FindElement(key).Update(value=config_opt_value)

        elif event in list(self.input_keys_to_config_name.keys()):
            for key, opt_name in self.input_keys_to_config_name.items():
                opt = self.selected_pipeline.parameters_group.get_config_option(opt_name)
                config_opt_value = opt.value()
                ui_value = values[key]
                if not str(config_opt_value) == ui_value or key == event:
                    ok, res = opt.validator.validate(ui_value)
                    if ok:
                        opt.set_value(ui_value)
                        window.FindElement(event).Update(background_color='White')
                    else:
                        window.FindElement(event).Update(background_color='Red')

    def tab_name(self) -> str:
        return self.pipeline_name

    def pipeline_frame_key(self):
        return pipeline_key(self.pipeline_name)

    def pipeline_config_input_key(self, config_name):
        return f'-IN-{self.pipeline_name}-{config_name}-'

    @property
    def reset_defaults_key(self):
        return f'-IN-{self.pipeline_name}-reset-'

    def get_opt_from_key(self, k) -> ConfigOption:
        pass


class PipelineSelectionLayout(TabLayout):
    def __init__(self, pipeline_manifest: PipelineManifest, event_key= '_pipeline_tab_'):
        self.pipeline_manifest = pipeline_manifest
        self.selected_pipeline = None

        # gui element identifier keys
        self.event_key = event_key
        self.combobox_key = '%s_combobox' % self.event_key
        self.select_pipeline_key = '%s_select_button' % self.event_key
        self.reset_defaults_key = '%s_reset_defaults_button' % self.event_key


        # create pipeline config layouts
        self.config_frames = {}
        for p in self.pipeline_manifest.list_pipeline_names():
            layout = PipelineConfigLayout(p, self.pipeline_manifest)
            self.config_frames[layout.pipeline_frame_key()] = layout



    def get_layout(self):
        pipelines = self.pipeline_manifest.list_pipeline_names()
        width = len(max(pipelines, key=len)) + 5
        frames = []
        for frame_key, pipeline_layout in self.config_frames.items():
            l = pipeline_layout.get_layout()
            n = pipeline_layout.pipeline_name
            frames.append(sg.Frame(n,l, key=frame_key, visible=False, font=Fonts.title_small))
        default_value = '<select a pipeline>'
        return [
                [sg.Text('Select and Configure a pipeline.', font=Fonts.description)],
                [sg.InputCombo(values=[default_value]+pipelines, size=(width, min(10, len(pipelines)+1)), default_value=default_value, key=self.combobox_key, font=Fonts.description),
                sg.Button('Select', key=self.select_pipeline_key)],
                frames
               ]



    # event loop handler
    def handle(self, window, event, values):
        if event == self.select_pipeline_key:
            selected_pipeline_name = values[self.combobox_key]
            if selected_pipeline_name == '<select a pipeline>' or selected_pipeline_name == '':
                return
            self.selected_pipeline = self.pipeline_manifest[selected_pipeline_name]

            # config_layout = self.create_config()


            frame_key = pipeline_key(selected_pipeline_name)
            window[frame_key](visible=True)
            for p in self.pipeline_manifest.list_pipeline_names():
                if p != selected_pipeline_name:
                    window[pipeline_key(p)](visible=False)
            # window.extend_layout(window['-COL1-'], config_layout)
            print('selected %s' % selected_pipeline_name)
            # self.create_config()
        else:
            for pipe_layout in self.config_frames.values():
                if event in pipe_layout.event_keys:
                    pipe_layout.handle(window, event, values)
                    break


    def tab_name(self):
        return 'Pipeline Selection'